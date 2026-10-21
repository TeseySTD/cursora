// Dev harness entry (index.html). Module scripts have no document.currentScript, so mount explicitly.
import { mountWidget } from "./mount";

const slot = document.getElementById("cursora-slot");
if (slot) mountWidget(slot, { siteKey: "dev-site-key" });
