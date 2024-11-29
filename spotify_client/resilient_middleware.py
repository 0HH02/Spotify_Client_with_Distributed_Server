import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import streamlit as st
from config import BASE_URLS


class ResilientRequestMiddleware:
    def __init__(self):
        self.base_urls = BASE_URLS

    def get(self, url_path, params=None, stream=False, headers=None):
        for base_url in self.base_urls:
            try:
                response = requests.get(
                    f"{base_url}{url_path}",
                    params=params,
                    stream=stream,
                    headers=headers,
                )
                if response.status_code == 200 or response.status_code == 206:
                    return response
            except (ConnectionError, Timeout) as e:
                print(f"Error connecting to {base_url}: {e}")
                continue
            except RequestException as e:
                print(f"An unexpected error occurred: {e}")
                continue
        st.error("All servers are currently unavailable.")
        return None
