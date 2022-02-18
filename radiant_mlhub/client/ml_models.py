from typing import Any, Dict, List, Optional, cast
from ..session import get_session
from requests.exceptions import HTTPError
from ..exceptions import EntityDoesNotExist, MLHubException


def get_model_by_id(model_id: str, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /models/{model_id}`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    model_id : str
        The ID of the ML Model to fetch
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Returns
    -------
    model : dict
    """
    session = get_session(api_key=api_key, profile=profile)
    try:
        return cast(Dict[str, Any], session.get(f'models/{model_id}').json())
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(f'MLModel "{model_id}" does not exist.') from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})') from None


def list_models(
    *,
    api_key: Optional[str] = None,
    profile: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Gets a list of JSON-like dictionaries representing ML Model objects returned by the Radiant MLHub ``GET /models`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Returns
    -------
    models : List[dict]
    """
    session = get_session(api_key=api_key, profile=profile)
    response = session.get('models')
    return cast(List[Dict[str, Any]], response.json())
