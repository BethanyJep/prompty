import abc
from .tracer import trace
from .core import Prompty
from typing import Callable, Dict, Literal


class Invoker(abc.ABC):
    """Abstract class for Invoker

    Attributes
    ----------
    prompty : Prompty
        The prompty object
    name : str
        The name of the invoker

    """

    def __init__(self, prompty: Prompty) -> None:
        self.prompty = prompty
        self.name = self.__class__.__name__

    @abc.abstractmethod
    def invoke(self, data: any) -> any:
        """Abstract method to invoke the invoker

        Parameters
        ----------
        data : any
            The data to be invoked

        Returns
        -------
        any
            The invoked
        """
        pass

    @abc.abstractmethod
    async def invoke_async(self, data: any) -> any:
        """Abstract method to invoke the invoker asynchronously

        Parameters
        ----------
        data : any
            The data to be invoked

        Returns
        -------
        any
            The invoked
        """
        pass

    @trace
    def run(self, data: any) -> any:
        """Method to run the invoker

        Parameters
        ----------
        data : any
            The data to be invoked

        Returns
        -------
        any
            The invoked
        """
        return self.invoke(data)

    @trace
    async def run_async(self, data: any) -> any:
        """Method to run the invoker asynchronously

        Parameters
        ----------
        data : any
            The data to be invoked

        Returns
        -------
        any
            The invoked
        """
        return await self.invoke_async(data)


class InvokerFactory:
    """Factory class for Invoker"""

    _renderers: Dict[str, Invoker] = {}
    _parsers: Dict[str, Invoker] = {}
    _executors: Dict[str, Invoker] = {}
    _processors: Dict[str, Invoker] = {}

    @classmethod
    def add_renderer(cls, name: str, invoker: Invoker) -> None:
        cls._renderers[name] = invoker

    @classmethod
    def add_parser(cls, name: str, invoker: Invoker) -> None:
        cls._parsers[name] = invoker

    @classmethod
    def add_executor(cls, name: str, invoker: Invoker) -> None:
        cls._executors[name] = invoker

    @classmethod
    def add_processor(cls, name: str, invoker: Invoker) -> None:
        cls._processors[name] = invoker

    @classmethod
    def register_renderer(cls, name: str) -> Callable:
        def inner_wrapper(wrapped_class: Invoker) -> Callable:
            cls._renderers[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def register_parser(cls, name: str) -> Callable:
        def inner_wrapper(wrapped_class: Invoker) -> Callable:
            cls._parsers[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def register_executor(cls, name: str) -> Callable:
        def inner_wrapper(wrapped_class: Invoker) -> Callable:
            cls._executors[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def register_processor(cls, name: str) -> Callable:
        def inner_wrapper(wrapped_class: Invoker) -> Callable:
            cls._processors[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def _get_name(
        cls,
        type: Literal["renderer", "parser", "executor", "processor"],
        prompty: Prompty,
    ) -> str:
        if type == "renderer":
            return prompty.template.type
        elif type == "parser":
            return f"{prompty.template.parser}.{prompty.model.api}"
        elif type == "executor":
            return prompty.model.configuration["type"]
        elif type == "processor":
            return prompty.model.configuration["type"]
        else:
            raise ValueError(f"Type {type} not found")

    @classmethod
    def _get_invoker(
        cls,
        type: Literal["renderer", "parser", "executor", "processor"],
        prompty: Prompty,
    ) -> Invoker:
        if type == "renderer":
            name = prompty.template.type
            if name not in cls._renderers:
                raise ValueError(f"Renderer {name} not found")

            return cls._renderers[name](prompty)

        elif type == "parser":
            name = f"{prompty.template.parser}.{prompty.model.api}"
            if name not in cls._parsers:
                raise ValueError(f"Parser {name} not found")

            return cls._parsers[name](prompty)

        elif type == "executor":
            name = prompty.model.configuration["type"]
            if name not in cls._executors:
                raise ValueError(f"Executor {name} not found")

            return cls._executors[name](prompty)

        elif type == "processor":
            name = prompty.model.configuration["type"]
            if name not in cls._processors:
                raise ValueError(f"Processor {name} not found")

            return cls._processors[name](prompty)

        else:
            raise ValueError(f"Type {type} not found")

    @classmethod
    def run(
        cls,
        type: Literal["renderer", "parser", "executor", "processor"],
        prompty: Prompty,
        data: any,
        default: any = None,
    ):
        name = cls._get_name(type, prompty)
        if name.startswith("NOOP") and default != None:
            return default
        elif name.startswith("NOOP"):
            return data

        invoker = cls._get_invoker(type, prompty)
        value = invoker.run(data)
        return value

    @classmethod
    async def run_async(
        cls,
        type: Literal["renderer", "parser", "executor", "processor"],
        prompty: Prompty,
        data: any,
        default: any = None,
    ):
        name = cls._get_name(type, prompty)
        if name.startswith("NOOP") and default != None:
            return default
        elif name.startswith("NOOP"):
            return data
        invoker = cls._get_invoker(type, prompty)
        value = await invoker.run_async(data)
        return value

    @classmethod
    def run_renderer(cls, prompty: Prompty, data: any, default: any = None) -> any:
        return cls.run("renderer", prompty, data, default)

    @classmethod
    async def run_renderer_async(
        cls, prompty: Prompty, data: any, default: any = None
    ) -> any:
        return await cls.run_async("renderer", prompty, data, default)

    @classmethod
    def run_parser(cls, prompty: Prompty, data: any, default: any = None) -> any:
        return cls.run("parser", prompty, data, default)

    @classmethod
    async def run_parser_async(
        cls, prompty: Prompty, data: any, default: any = None
    ) -> any:
        return await cls.run_async("parser", prompty, data, default)

    @classmethod
    def run_executor(cls, prompty: Prompty, data: any, default: any = None) -> any:
        return cls.run("executor", prompty, data, default)

    @classmethod
    async def run_executor_async(
        cls, prompty: Prompty, data: any, default: any = None
    ) -> any:
        return await cls.run_async("executor", prompty, data, default)

    @classmethod
    def run_processor(cls, prompty: Prompty, data: any, default: any = None) -> any:
        return cls.run("processor", prompty, data, default)

    @classmethod
    async def run_processor_async(
        cls, prompty: Prompty, data: any, default: any = None
    ) -> any:
        return await cls.run_async("processor", prompty, data, default)


class InvokerException(Exception):
    """Exception class for Invoker"""

    def __init__(self, message: str, type: str) -> None:
        super().__init__(message)
        self.type = type

    def __str__(self) -> str:
        return f"{super().__str__()}. Make sure to pip install any necessary package extras (i.e. could be something like `pip install prompty[{self.type}]`) for {self.type} as well as import the appropriate invokers (i.e. could be something like `import prompty.{self.type}`)."


@InvokerFactory.register_renderer("NOOP")
@InvokerFactory.register_parser("NOOP")
@InvokerFactory.register_executor("NOOP")
@InvokerFactory.register_processor("NOOP")
@InvokerFactory.register_parser("prompty.embedding")
@InvokerFactory.register_parser("prompty.image")
@InvokerFactory.register_parser("prompty.completion")
class NoOp(Invoker):
    def invoke(self, data: any) -> any:
        return data

    async def invoke_async(self, data: str) -> str:
        return self.invoke(data)
