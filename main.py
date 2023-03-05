#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import uuid
import time
import requests
import logging
from datetime import datetime, date

from configparser import ConfigParser
from sys import platform

import pytak
import json


class MySerializer(pytak.QueueWorker):
    """
    Defines how you process or generate your Cursor-On-Target Events.
    From there it adds the COT Events to a queue for TX to a COT_URL.
    """

    async def handle_data(self, data):
        """
        Handles pre-COT data and serializes to COT Events, then puts on queue.
        """
        event = data
        await self.put_queue(event)

    async def run(self, number_of_iterations=-1):
        """
        Runs the loop for processing or generating pre-COT data.
        """
        logger = logging.getLogger("l360tocot")
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
        base_url = "https://api.life360.com/v3/"
        token_url = "oauth2/token.json"
        circles_url = "circles/"
        username = self.config.get("L360_USER_NAME")
        password = self.config.get("L360_PASSWORD")
        api_auth_token = self.config.get("L360_AUTH_TOKEN")
        get_all_circles = self.config.getboolean("L360_GET_ALL_CIRCLES")
        a_token = authenticate(base_url, token_url, username, password, api_auth_token)
        while True:
            try:
                poll_interval: int = int(self.config.get("POLL_INTERVAL"))
                members = {}
                circles = []
                a_circles = get_circles(base_url, circles_url, a_token)
                if get_all_circles:
                    for i in a_circles:
                        circles.append(get_circle(base_url, circles_url, a_token, i))
                else:
                    a_circles = a_circles[0]
                    circles.append(
                        get_circle(base_url, circles_url, a_token, a_circles["id"])
                    )
                for i in circles:
                    name_circle = i["name"]
                    temp_members = i["members"]
                    for i2 in temp_members:
                        if i2["location"] == None:
                            continue
                        else:
                            loc = i2["location"]
                        members[f"{i2['firstName']} {i2['lastName']}"] = {
                            "lat": loc["latitude"],
                            "lon": loc["longitude"],
                            "battery": loc["battery"],
                            "id": i2["id"],
                            "phone": i2["loginPhone"][1:]
                        }
                for name, data in members.items():
                    data = tak_memberUpdate(data, name, name_circle, poll_interval)
                    await self.handle_data(data)
                logger.info(
                    f"Updated {len(members)} members positions! Checking in {int(poll_interval) // 60} minutes..."
                )
                await asyncio.sleep(int(poll_interval))
            except:
                raise Exception("Error detected! Shutting down to prevent API spam.")


def make_request(url, params=None, method="GET", authheader=None):
    headers = {"Accept": "application/json"}
    if authheader:
        headers.update(
            {
                "Authorization": authheader,
                "cache-control": "no-cache",
            }
        )

    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, data=params, headers=headers)

    return r.json()


def authenticate(base_url, token_url, username, password, authorization_token):
    url = base_url + token_url
    params = {
        "grant_type": "password",
        "phone": username,
        "password": password,
        "countryCode": 1,
    }

    r = make_request(
        url=url, params=params, method="POST", authheader="Basic " + authorization_token
    )
    try:
        access_token = r["access_token"]
        return access_token
    except:
        return None


def get_circles(base_url, circles_url, access_token):
    url = base_url + circles_url
    authheader = "bearer " + access_token
    r = make_request(url=url, method="GET", authheader=authheader)
    return r["circles"]


def get_circle(base_url, circle_url, access_token, circle_id):
    url = base_url + circle_url + circle_id
    authheader = "bearer " + access_token
    r = make_request(url=url, method="GET", authheader=authheader)
    return r


def tak_memberUpdate(data, name, name_circle, poll_interval):
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-f-G-U-C")
    root.set("uid", data["id"])
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(int(poll_interval)))

    point = ET.SubElement(root, "point")
    point.set("lat", str(data["lat"]))
    point.set("lon", str(data["lon"]))
    point.set("hae", "250")
    point.set("ce", "9999999.0")
    point.set("le", "9999999.0")

    detail = ET.SubElement(root, "detail")

    status = ET.SubElement(detail, "status")
    status.set("battery", data["battery"])

    group = ET.SubElement(detail, "__group")
    group.set("role", "Team Member")
    group.set("role", "Cyan")

    remarks = ET.SubElement(detail, "remarks")
    remarks.text = f"Circle: {name_circle}"

    precisionlocation = ET.SubElement(detail, "precisionlocation")
    precisionlocation.set("altsrc", "GPS")
    precisionlocation.set("geopointsrc", "GPS")

    contact = ET.SubElement(detail, "contact")
    contact.set("callsign", name)
    contact.set("phone", data["phone"])

    return ET.tostring(root)


async def main():
    """
    The main definition of your program, sets config params and
    adds your serializer to the asyncio task list.
    """

    config = ConfigParser()
    config.read("config.ini")
    config = config["l360tocot"]
    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add your serializer to the asyncio task list.
    clitool.add_tasks(set([MySerializer(clitool.tx_queue, config)]))
    # Start all tasks.
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
