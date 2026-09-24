# DLC content vs Doomsday (investigation result)
#
# CAN script copies unlock DLC without owning it?
#   PARTIAL. Copying common/* scripts and replacing has_dlc with always=yes
#   only helps for features the ENGINE already runs from script.
#   Steam "Active DLC" still locks some UI/systems (LaR operatives/ops topbar,
#   AAT CIC international market payment). Those cannot be forced by file copies.
#
# RAIDS — KEEP
#   Introduced with Götterdämmerung patch 1.15 as a FREE update system.
#   Owning the paid Gotter expansion is NOT required for the baseline raid UI.
#   Mod copies in common/raids/ are ungated/customized and stay in the mod.
#   Some raid *targets* tied to paid special projects still need those projects.
#
# SPECIAL PROJECTS / SCIENTISTS — KEEP
#   Baseline facilities + projects are free-update content. Mod copies stay.
#   Facility buildings use dlc_allowed = { always = yes }.
#
# REMOVED (copy approach does not deliver full DLC without ownership):
#   - LaR operations / phases / tokens / intelligence_agencies / upgrades
#   - LaR agency bootstrap decisions (create_intelligence_agency ≠ full LaR)
#   - zz_dlc_* on_actions (LAR/NSB/BBA/AAT/WUW/TAOG) — focus noise, no unlock
#   - timed_activities (stage coup), equipment_groups MIO stubs from port
#
# USE INSTEAD (Doomsday systems, no DLC):
#   - Covert missions: common/decisions/doomsday_intel*
#   - Buy/sell equipment: Arms Market (treasury) on the economy panel
#   - Mercenaries: Doomsday merc market
#
# fulldlcfiles/ remains art/reference only — not loaded as playable DLC.
