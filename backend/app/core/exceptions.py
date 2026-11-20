from fastapi import HTTPException, status


class CampusFixException(Exception):
    """Base domain exception for CampusFix"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(HTTPException):
    def __init__(self, entity_name: str, identifier: any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with identifier '{identifier}' not found."
        )


class UnauthorizedAccessException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenOperationException(HTTPException):
    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class InvalidStateTransitionException(HTTPException):
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition complaint from '{current_status}' to '{target_status}'."
        )


class DuplicateResourceException(HTTPException):
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} with {field} '{value}' already exists."
        )
