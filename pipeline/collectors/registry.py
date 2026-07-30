from __future__ import annotations

from pipeline.collectors.base import Collector
from pipeline.collectors.bizinfo import BizinfoCollector
from pipeline.collectors.dev_event import DevEventCollector
from pipeline.collectors.eventus import EventusCollector
from pipeline.collectors.html import StructuredHtmlCollector
from pipeline.collectors.kocca import KoccaCollector
from pipeline.collectors.kstartup import KStartupCollector
from pipeline.collectors.linkareer import LinkareerCollector
from pipeline.collectors.nipa import NipaCollector
from pipeline.collectors.gcon import GconCollector
from pipeline.collectors.thinkcontest import ThinkContestCollector
from pipeline.collectors.wevity import WevityCollector
from pipeline.config import SourceConfig
from pipeline.http import HttpClient


def create_collector(config: SourceConfig, client: HttpClient | None = None) -> Collector:
    if config.id == "bizinfo":
        return BizinfoCollector(config, client)
    if config.id == "dev_event":
        return DevEventCollector(config, client)
    if config.id == "eventus":
        return EventusCollector(config, client)
    if config.id == "kocca":
        return KoccaCollector(config, client)
    if config.id == "kstartup":
        return KStartupCollector(config, client)
    if config.id == "linkareer":
        return LinkareerCollector(config, client)
    if config.id == "thinkcontest":
        return ThinkContestCollector(config, client)
    if config.id == "wevity":
        return WevityCollector(config, client)
    if config.id == "gcon":
        return GconCollector(config, client)
    if config.id == "nipa":
        return NipaCollector(config, client)
    return StructuredHtmlCollector(config, client)
