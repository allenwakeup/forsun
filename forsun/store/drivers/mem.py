# -*- coding: utf-8 -*-
# 18/1/25
# create by: snower

import time
import logging
from collections import defaultdict
import msgpack
from tornado import gen
from ...plan import Plan
from ..store import Store
from ... import config

class MemStore(Store):
    def __init__(self, *args, **kwargs):
        super(MemStore, self).__init__(*args, **kwargs)

        self.plans = {}
        self.time_plans = defaultdict(dict)
        self.current_time = int(time.time())
        self.store_file = config.get("STORE_MEM_STORE_FILE", "/tmp/forsun.session")

    @gen.coroutine
    def init(self):
        try:
            with open(self.store_file, "rb") as fp:
                data = fp.read()
                data = msgpack.loads(data, encoding = "utf-8")
                self.plans = {}
                for plan in data.get("plans", []):
                    plan = Plan.loads(plan)
                    self.plans[plan.key] = plan

                self.time_plans = defaultdict(dict)
                for key, plans in data.get("time_plans", {}):
                    self.time_plans[key] = {key: self.plans[key] for key in (plans or []) if key in self.plans}
                self.current_time = data.get("current_time", self.current_time)
            logging.info("store mem load session %s", self.store_file)
        except Exception as e:
            logging.error("store mem load session error: %s %s", self.store_file, e)

    @gen.coroutine
    def uninit(self):
        try:
            with open(self.store_file, "wb") as fp:
                data = msgpack.dumps({
                    "plans": [plan.dumps() for key, plan in self.plans.items()],
                    "time_plans": {ts: list(plans.keys()) for ts, plans in self.time_plans.items()},
                    "current_time": self.current_time,
                })
                fp.write(data)
            logging.info("store mem save session %s", self.store_file)
        except Exception as e:
            logging.error("store mem save session error: %s %s", self.store_file, e)

    @gen.coroutine
    def set_current(self, current_time):
        self.current_time = current_time
        raise gen.Return(self.current_time)

    @gen.coroutine
    def get_current(self):
        raise gen.Return(self.current_time)

    @gen.coroutine
    def set_plan(self, plan):
        self.plans[plan.key] = plan
        raise gen.Return(plan)

    @gen.coroutine
    def remove_plan(self, key):
        if key in self.plans:
            raise gen.Return(self.plans.pop(key))
        raise gen.Return(None)

    @gen.coroutine
    def get_plan(self, key):
        if key in self.plans:
            raise gen.Return(self.plans[key])
        raise gen.Return(None)

    @gen.coroutine
    def add_time_plan(self, plan):
        self.time_plans[plan.next_time][plan.key] = plan
        raise gen.Return(plan)

    @gen.coroutine
    def get_time_plan(self, ts):
        raise gen.Return(self.time_plans[ts].keys())

    @gen.coroutine
    def remove_time_plan(self, plan):
        if plan.key in self.time_plans[plan.next_time]:
            raise gen.Return(self.time_plans[plan.next_time].pop(plan.key))
        raise gen.Return(None)

    @gen.coroutine
    def delete_time_plan(self, ts):
        if ts in self.time_plans:
            raise gen.Return(self.time_plans.pop(ts))
        raise gen.Return(None)

    @gen.coroutine
    def get_plan_keys(self, prefix = ""):
        keys = []
        for key in self.plans:
            if key.startswith(prefix):
                keys.append(key)
        raise gen.Return(keys)