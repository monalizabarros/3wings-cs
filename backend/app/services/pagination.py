from sqlalchemy.orm import Query as SAQuery


def paginate(query: SAQuery, page: int, page_size: int) -> tuple[list, int]:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
