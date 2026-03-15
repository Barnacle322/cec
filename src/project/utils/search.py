from __future__ import annotations

from flask import current_app

from ..extenstions import meili

INDEX_NAME = "courses"
_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_EMBEDDING_DIMS = 384

_model = None


def _get_embedding(text: str) -> list[float]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_EMBEDDING_MODEL)
    return _model.encode(text).tolist()


def build_document(course) -> dict:
    from ..models import Timetable

    timetables = Timetable.get_by_course_id(course.id)

    name_ru = course._name.get("ru", "") if course._name else ""
    name_en = course._name.get("en", "") if course._name else ""
    desc_ru = course._description.get("ru", "") if course._description else ""
    desc_en = course._description.get("en", "") if course._description else ""

    group_slug = course.course_group.slug if course.course_group else ""

    doc = {
        "id": course.id,
        "slug": course.slug,
        "picture_url": course.picture_url,
        "course_group_id": course.course_group_id,
        "course_group_slug": group_slug,
        "name_ru": name_ru,
        "name_en": name_en,
        "description_ru": desc_ru,
        "description_en": desc_en,
        "timetable_names_ru": " ".join(t._name.get("ru", "") for t in timetables if t._name),
        "timetable_names_en": " ".join(t._name.get("en", "") for t in timetables if t._name),
    }

    embedding_text = f"{name_ru} {name_en} {desc_ru}".strip()
    vector = _get_embedding(embedding_text)
    doc["_vectors"] = {"course_embedder": vector}

    return doc


def configure_index() -> None:
    try:
        meili.client.create_index(INDEX_NAME, {"primaryKey": "id"})
    except Exception:
        pass  # index already exists

    try:
        import requests as _requests

        cfg = meili.client.config
        _requests.patch(
            f"{cfg.url}/experimental-features",
            json={"vectorStore": True},
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout=5,
        ).raise_for_status()
    except Exception:
        current_app.logger.warning("[search] Failed to enable vector store experimental feature", exc_info=True)

    try:
        idx = meili.client.index(INDEX_NAME)
        idx.update_searchable_attributes([
            "name_ru", "name_en",
            "description_ru", "description_en",
            "timetable_names_ru", "timetable_names_en",
        ])
        idx.update_filterable_attributes(["course_group_id", "course_group_slug"])
        idx.update_embedders({
            "course_embedder": {
                "source": "userProvided",
                "dimensions": _EMBEDDING_DIMS,
            }
        })
    except Exception:
        current_app.logger.warning("[search] Failed to configure Meilisearch index", exc_info=True)


def index_course(course) -> None:
    try:
        doc = build_document(course)
        meili.client.index(INDEX_NAME).add_documents([doc], primary_key="id")
    except Exception:
        current_app.logger.warning(f"[search] Failed to index course {course.id}", exc_info=True)


def delete_course(course_id: int) -> None:
    try:
        meili.client.index(INDEX_NAME).delete_document(course_id)
    except Exception:
        current_app.logger.warning(f"[search] Failed to delete course {course_id} from index", exc_info=True)


def reindex_all_courses() -> int:
    from ..models import Course

    courses = Course.get_all()
    docs = []
    for course in courses:
        try:
            docs.append(build_document(course))
        except Exception:
            current_app.logger.warning(f"[search] Failed to build document for course {course.id}", exc_info=True)

    if docs:
        meili.client.index(INDEX_NAME).add_documents(docs, primary_key="id")

    return len(docs)
