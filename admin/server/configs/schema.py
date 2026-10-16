"""任务配置的强类型模型，与 config.json 中 targets / stickers 的格式一一对应。

后台只编辑好友和表情；task_id、发送间隔等其他字段由 store 原样保留。
"""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextMessage(_Strict):
    type: Literal["text"]
    content: Text


class StickerMessage(_Strict):
    type: Literal["douyin_sticker"]
    sticker: Name


class ImageMessage(_Strict):
    type: Literal["image"]
    path: Name


SimpleMessage = Annotated[Union[TextMessage, StickerMessage, ImageMessage], Field(discriminator="type")]


class RandomMessage(_Strict):
    type: Literal["random"]
    choices: list[SimpleMessage] = Field(min_length=1, max_length=50)


Message = Annotated[
    Union[TextMessage, StickerMessage, ImageMessage, RandomMessage], Field(discriminator="type")
]


class Friend(_Strict):
    name: Name
    enabled: bool = True
    messages: list[Message] = Field(min_length=1, max_length=20)


class Sticker(_Strict):
    label: Name | None = None
    accessible_name: Name | None = None
    category: Name | None = None
    fallback_index: int | None = Field(default=None, ge=0)


class FriendsConfig(_Strict):
    """后台读写的配置视图。version 是读取时的文件指纹，保存时用来发现并发修改。"""

    friends: list[Friend] = Field(max_length=200)
    stickers: dict[Name, Sticker] = Field(default_factory=dict)
    version: str
