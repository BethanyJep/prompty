import base64
import re
from pathlib import Path

from .core import Prompty
from .invoker import Invoker


class PromptyChatParser(Invoker):
    """Prompty Chat Parser"""

    def __init__(self, prompty: Prompty) -> None:
        super().__init__(prompty)
        self.roles = ["assistant", "function", "system", "user"]
        if isinstance(self.prompty.file, str):
            self.prompty.file = Path(self.prompty.file).resolve().absolute()

        self.path = self.prompty.file.parent

    def inline_image(self, image_item: str) -> str:
        """Inline Image

        Parameters
        ----------
        image_item : str
            The image item to inline

        Returns
        -------
        str
            The inlined image
        """
        # pass through if it's a url or base64 encoded
        if image_item.startswith("http") or image_item.startswith("data"):
            return image_item
        # otherwise, it's a local file - need to base64 encode it
        else:
            image_path = self.path / image_item
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

            if image_path.suffix == ".png":
                return f"data:image/png;base64,{base64_image}"
            elif image_path.suffix == ".jpg":
                return f"data:image/jpeg;base64,{base64_image}"
            elif image_path.suffix == ".jpeg":
                return f"data:image/jpeg;base64,{base64_image}"
            else:
                raise ValueError(
                    f"Invalid image format {image_path.suffix} - currently only .png and .jpg / .jpeg are supported."
                )

    def parse_content(self, content: str):
        """for parsing inline images

        Parameters
        ----------
        content : str
            The content to parse

        Returns
        -------
        any
            The parsed content
        """
        # regular expression to parse markdown images
        image = r"(?P<alt>!\[[^\]]*\])\((?P<filename>.*?)(?=\"|\))\)"
        matches = re.findall(image, content, flags=re.MULTILINE)
        if len(matches) > 0:
            content_items = []
            content_chunks = re.split(image, content, flags=re.MULTILINE)
            current_chunk = 0
            for i in range(len(content_chunks)):
                # image entry
                if (
                    current_chunk < len(matches)
                    and content_chunks[i] == matches[current_chunk][0]
                ):
                    content_items.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self.inline_image(
                                    matches[current_chunk][1].split(" ")[0].strip()
                                )
                            },
                        }
                    )
                # second part of image entry
                elif (
                    current_chunk < len(matches)
                    and content_chunks[i] == matches[current_chunk][1]
                ):
                    current_chunk += 1
                # text entry
                else:
                    if len(content_chunks[i].strip()) > 0:
                        content_items.append(
                            {"type": "text", "text": content_chunks[i].strip()}
                        )
            return content_items
        else:
            return content

    def invoke(self, data: str) -> list[dict[str, str]]:
        """Invoke the Prompty Chat Parser

        Parameters
        ----------
        data : str
            The data to parse

        Returns
        -------
        str
            The parsed data
        """
        messages = []
        separator = r"(?i)^\s*#?\s*(" + "|".join(self.roles) + r")\s*:\s*\n"

        # get valid chunks - remove empty items
        chunks = [
            item
            for item in re.split(separator, data, flags=re.MULTILINE)
            if len(item.strip()) > 0
        ]

        # if no starter role, then inject system role
        if chunks[0].strip().lower() not in self.roles:
            chunks.insert(0, "system")

        # if last chunk is role entry, then remove (no content?)
        if chunks[-1].strip().lower() in self.roles:
            chunks.pop()

        if len(chunks) % 2 != 0:
            raise ValueError("Invalid prompt format")

        # create messages
        for i in range(0, len(chunks), 2):
            role = chunks[i].strip().lower()
            content = chunks[i + 1].strip()
            messages.append({"role": role, "content": self.parse_content(content)})

        return messages

    async def invoke_async(self, data: str) -> list[dict[str, str]]:
        """Invoke the Prompty Chat Parser (Async)

        Parameters
        ----------
        data : str
            The data to parse

        Returns
        -------
        str
            The parsed data
        """
        return self.invoke(data)
