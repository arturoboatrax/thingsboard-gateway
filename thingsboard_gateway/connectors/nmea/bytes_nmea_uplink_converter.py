#     Copyright 2020. ThingsBoard
#
#     Licensed under the Apache License, Version 2.0 (the "License"];
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import struct

from thingsboard_gateway.connectors.converter import log
from thingsboard_gateway.connectors.nmea.nmea_converter import NmeaConverter


class BytesNmeaUplinkConverter(NmeaConverter):
    def convert(self, configs, can_data):
        result = {"attributes": {},
                  "telemetry": {}}

        for config in configs:
            try:
                tb_key = config["key"]
                tb_item = "telemetry" if config["is_ts"] else "attributes"

                # The 'value' variable is used in eval
                if config["type"][0] == "b":
                    value = bool(can_data[config["start"]])
                elif config["type"][0] == "i" or config["type"][0] == "l":
                    value = int.from_bytes(can_data[config["start"]:config["start"] + config["length"]],
                                           config["byteorder"],
                                           signed=config["signed"])
                elif config["type"][0] == "f" or config["type"][0] == "d":
                    fmt = ">" + config["type"][0] if config["byteorder"][0] == "b" else "<" + config["type"][0]
                    value = struct.unpack_from(fmt,
                                               bytes(can_data[config["start"]:config["start"] + config["length"]]))[0]
                elif config["type"][0] == "s":
                    value = can_data[config["start"]:config["start"] + config["length"]].decode(config["encoding"])
                else:
                    log.error("Failed to convert NMEA data to TB %s '%s': unknown data type '%s'",
                              "time series key" if config["is_ts"] else "attribute", tb_key, config["type"])
                    continue

                if config.get("expression", ""):
                    result[tb_item][tb_key] = eval(config["expression"],
                                                   {"__builtins__": {}} if config["strictEval"] else globals(),
                                                   {"value": value, "nmea_data": can_data})
                else:
                    result[tb_item][tb_key] = value
            except Exception as e:
                log.error("Failed to convert NMEA data to TB %s '%s': %s",
                          "time series key" if config["is_ts"] else "attribute", tb_key, str(e))
                continue
        return result
