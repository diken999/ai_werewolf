from __future__ import annotations

import os
from functools import lru_cache
from typing import TypeVar

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_env() -> None:
    """优先加载本项目 .env，再尝试复用 langchain_study 的 .env。"""
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(here, ".env"))
    study_env = os.path.join(os.path.dirname(here), "langchain_study", ".env")
    load_dotenv(study_env, override=False)


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    load_env()
    return init_chat_model(
        model="deepseek-flash",
        extra_body={"thinking": {"type": "disabled"}},
    )


def structured_invoke(schema: type[T], system: str, user: str) -> T:
    llm = get_llm().with_structured_output(schema)
    return llm.invoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
