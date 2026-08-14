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

def _build_campanas_view(
    build_campanas_admin_view,
    build_campanas_gerente_view,
    es_admin
):
    if es_admin():
        return build_campanas_admin_view()
    else:
        return build_campanas_gerente_view()