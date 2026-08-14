import flet as ft
import os
import re
import json
import time
import threading
import datetime
import requests
import base64
import math
import asyncio
import csv
import subprocess
import tempfile
import shutil
import random
import calendar
import flet_video as fv
from frontend.components.ui import EmojiIconButton, EmojiDropdown

def _build_subtab_diarias_view(
    diarias_container,
    tienda_label_diarias
):
    return ft.Column([
        tienda_label_diarias,
        diarias_container
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)