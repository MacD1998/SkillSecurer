# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MCP rug-pull analyzer stub node."""

# TODO(SADD B.3.3): Compare current vs previous manifest; emit RP1–RP3 when previous manifest available. See SADD for skillspector § B.3.3.

from __future__ import annotations

from skillspector.logging_config import get_logger
from skillspector.state import AnalyzerNodeResponse, SkillspectorState

ANALYZER_ID = "mcp_rug_pull"
logger = get_logger(__name__)


def node(state: SkillspectorState) -> AnalyzerNodeResponse:
    """Stub: no implementation yet; returns no findings."""
    logger.info("%s: 0 findings", ANALYZER_ID)
    logger.debug("%s: stub, returning no findings", ANALYZER_ID)
    return {"findings": []}
