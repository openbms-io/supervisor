from src.models.bacnet_config import get_latest_bacnet_config_json
from src.network.rest_client import RestClient
import logging
from src.models.controller_points import get_points_to_upload, mark_points_as_uploaded
from src.models.controller_points import ControllerPointsModel

logger = logging.getLogger(__name__)


async def upload_config(url: str, jwt_token: str):
    logger.info(f"Uploading config to {url} with jwtToken {jwt_token}")
    # 1. Fetch data from bacnet_config.py
    config = await get_latest_bacnet_config_json()

    if not config or not config.bacnet_devices:
        logging.warning("No BACnet config found to upload.")
        return None

    logging.info(f"config being uploaded: {config.bacnet_devices}")
    # 2. Upload the fetched json to the url via POST
    async with RestClient(jwt_token=jwt_token) as rest_client:
        response = await rest_client.post(url, json={"config": config.bacnet_devices})
        if response:
            logging.info(f"Upload config response: {response.json()}")
        else:
            logging.error("Failed to upload config. No response received from server.")
    return response


async def get_points_to_publish():
    # 1. Fetch data from controller_points.py
    points = await get_points_to_upload()
    if not points:
        logging.warning("No points found to publish.")
        return None

    return points


async def mark_points_as_uploaded_in_db(points: list[ControllerPointsModel]):
    await mark_points_as_uploaded(points)
