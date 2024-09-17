import json
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, ConfigDict, Field

from phi.utils.log import logger


class Message(BaseModel):
    """Message sent to the Model"""

    # The role of the message author.
    # One of system, user, assistant, or tool.
    role: str
    # The contents of the message. content is required for all messages,
    # and may be null for assistant messages with function calls.
    content: Optional[Union[List[Dict], str]] = None
    # An optional name for the participant.
    # Provides the model information to differentiate between participants of the same role.
    name: Optional[str] = None
    # Tool call that this message is responding to.
    tool_call_id: Optional[str] = None
    # The error of the tool call
    tool_call_error: Optional[bool] = None
    # The name of the tool called
    tool_name: Optional[str] = Field(None, alias="tool_call_name")
    # Arguments passed to the tool
    tool_args: Optional[Any] = Field(None, alias="tool_call_arguments")
    # The tool calls generated by the model, such as function calls.
    tool_calls: Optional[List[Dict[str, Any]]] = None
    # Metrics for the message, tokes + the time it took to generate the response.
    metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def get_content_string(self) -> str:
        """Returns the content as a string."""
        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, list):
            import json

            return json.dumps(self.content)
        return ""

    def to_dict(self) -> Dict[str, Any]:
        _dict = self.model_dump(exclude_none=True, exclude={"metrics", "tool_name", "tool_args", "tool_call_error"})
        # Manually add the content field if it is None
        if self.content is None:
            _dict["content"] = None
        return _dict

    def log(self, level: Optional[str] = None):
        """Log the message to the console

        @param level: The level to log the message at. One of debug, info, warning, or error.
            Defaults to debug.
        """
        _logger = logger.debug
        if level == "debug":
            _logger = logger.debug
        elif level == "info":
            _logger = logger.info
        elif level == "warning":
            _logger = logger.warning
        elif level == "error":
            _logger = logger.error

        _logger(f"============== {self.role} ==============")
        if self.name:
            _logger(f"Name: {self.name}")
        if self.tool_call_id:
            _logger(f"Call Id: {self.tool_call_id}")
        if self.content:
            _logger(self.content)
        if self.tool_calls:
            _logger(f"Tool Calls: {json.dumps(self.tool_calls, indent=2)}")
        # if self.model_extra and "images" in self.model_extra:
        #     _logger("images: {}".format(self.model_extra["images"]))

    def content_is_valid(self) -> bool:
        """Check if the message content is valid."""

        return self.content is not None and len(self.content) > 0
