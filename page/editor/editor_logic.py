import js
import json
import asyncio
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy

ALL_LICENSES = [
	"Avgi Atomics", "Avgi Torch", "Carrier", "City-Ship", "Coalition", "Cruiser",
	"Gegno Civilian", "Gegno Driller", "Heliarch", "Hicemus Conflict", "High Houses",
	"Militia", "Navy Auxiliary", "Navy Carrier", "Navy Cruiser", "Navy", "Pilot's",
	"Remnant Capital", "Remnant", "Scin Adjutant", "Scin Architect", "Scin Hoplologist",
	"Successor", "Twilight Guard", "Vi Centurion", "Vi Evocati", "Vi Lord", "Wanderer",
	"Wanderer Military", "Wanderer Outfits"
]

raw_content = ""
file_name = "savegame.txt"
current_ship_index = None
json_root_dict = {}
extracted_ships_by_cat = {}
all_global_ships = {}
all_global_missions = {}

state = {
	"pilotname": "", "date": "", "system": "", "planet": "",
	"prev_system": "", "prev_planet": "", "entry_method": "",
	"credits": 0, "reputations": {}, "licenses": set(), "ships": [], "plugins": [],
	"conditions": []
}

def mark_changed():
	"""Macht den Apply Changes Button sichtbar, sobald eine Änderung erfolgt ist."""
	save_btn = js.document.getElementById("save-btn")
	save_btn.classList.remove("hidden")

def extract_data_from_json(data_tree):
	categories = {}
	global all_global_ships, all_global_missions
	all_global_ships = {}
	all_global_missions = {}

	if not isinstance(data_tree, dict):
		return categories

	def search_nodes(tree):
		if isinstance(tree, dict):
			for k, v in tree.items():
				if k == "ship" and isinstance(v, dict):
					for ship_key, ship_data in v.items():
						if isinstance(ship_data, dict) and "code" in ship_data:
							all_global_ships[ship_key] = ship_data["code"]
				elif k == "mission" and isinstance(v, dict):
					for m_key, m_data in v.items():
						if isinstance(m_data, dict) and "code" in m_data:
							all_global_missions[m_key] = m_data["code"]
				else:
					search_nodes(v)

	search_nodes(data_tree)

	for cat_name, cat_content in data_tree.items():
		if not isinstance(cat_content, dict):
			continue

		ship_node = cat_content.get("ship")
		if isinstance(ship_node, dict):
			cat_ships = {}
			for ship_key, ship_data in ship_node.items():
				if isinstance(ship_data, dict) and "code" in ship_data:
					cat_ships[ship_key] = ship_data["code"]
			if cat_ships:
				categories[cat_name] = cat_ships

	return categories

async def load_remote_ship_data():
	global json_root_dict, extracted_ships_by_cat
	cat_select = js.document.getElementById("add-ship-category")
	target_url = "https://raw.githubusercontent.com/zuckung/ES-DataParser/main/page/data.json"
	
	try:
		response = await pyfetch(target_url)
		if response.status == 200:
			json_root_dict = await response.json()
			extracted_ships_by_cat = extract_data_from_json(json_root_dict)

			cat_select.innerHTML = '<option value="">-- Select Category / Race --</option>'
			for cat_key in sorted(extracted_ships_by_cat.keys()):
				opt = js.document.createElement("option")
				opt.value = cat_key
				opt.textContent = cat_key.replace('"', '')
				cat_select.appendChild(opt)
		else:
			cat_select.innerHTML = f'<option value="">Error {response.status} loading JSON</option>'
	except Exception as e:
		print(f"Fehler beim Laden der JSON: {e}")
		cat_select.innerHTML = '<option value="">Error loading data.json</option>'

def on_category_changed(event):
	cat_key = js.document.getElementById("add-ship-category").value
	model_select = js.document.getElementById("add-ship-model")
	add_btn = js.document.getElementById("add-ship-btn")
	preview_area = js.document.getElementById("add-ship-preview")
	
	model_select.innerHTML = '<option value="">-- Select Ship Model --</option>'
	preview_area.value = ""
	add_btn.disabled = True

	if not cat_key or cat_key not in extracted_ships_by_cat:
		model_select.disabled = True
		return

	ships_in_cat = extracted_ships_by_cat[cat_key]

	for ship_name in sorted(ships_in_cat.keys()):
		opt = js.document.createElement("option")
		opt.value = ship_name
		opt.textContent = ship_name.replace('"', '')
		model_select.appendChild(opt)

	model_select.disabled = False

def parse_es_blocks(code_str):
	"""Zerlegt einen Endless Sky Node-Code in hierarchische Blöcke und Einzel-Statements."""
	lines = code_str.splitlines()
	if not lines:
		return {}, [], ""

	first_line = lines[0]
	blocks = {}      # Schlüssel: Block-Name (z. B. "outfits", "attributes")
	statements = []  # Liste von Unterzeilen (Statement / Positionszeilen)

	current_block = None
	current_block_lines = []

	for line in lines[1:]:
		if not line.strip():
			continue
		
		indent_level = len(line) - len(line.lstrip('\t'))
		stripped = line.strip()

		if indent_level == 1:
			if stripped in ["attributes", "outfits", "weapon", "engine", "gun", "turret", "leak", "explode"]:
				if current_block:
					blocks[current_block] = current_block_lines
				current_block = stripped
				current_block_lines = [line]
			else:
				if current_block:
					blocks[current_block] = current_block_lines
					current_block = None
				statements.append(line)
		else:
			if current_block:
				current_block_lines.append(line)
			else:
				statements.append(line)

	if current_block:
		blocks[current_block] = current_block_lines

	return blocks, statements, first_line

def build_ship_syntax(selected_key, cat_key=""):
	"""Löst Vererbung & Overrides vollständig auf und setzt Runtime-Werte basierend auf den Attributen."""
	raw_code = ""
	if cat_key and cat_key in extracted_ships_by_cat:
		raw_code = extracted_ships_by_cat[cat_key].get(selected_key, "")

	if not raw_code and selected_key in all_global_ships:
		raw_code = all_global_ships[selected_key]

	if not raw_code:
		return ""

	lines = raw_code.splitlines()
	first_line = lines[0] if lines else f'ship "{selected_key}"'

	parts_quoted = [p for p in first_line.split('"') if p.strip()]
	
	base_ship_name = None
	if len(parts_quoted) >= 2 and parts_quoted[0].strip().startswith("ship"):
		base_ship_name = parts_quoted[1]

	merged_blocks = {}
	
	if base_ship_name and base_ship_name in all_global_ships and base_ship_name != selected_key.strip('"'):
		base_code = all_global_ships[base_ship_name]
		
		base_blocks, base_statements, base_header = parse_es_blocks(base_code)
		var_blocks, var_statements, var_header = parse_es_blocks(raw_code)

		final_lines = [f'ship "{base_ship_name}"', '\tname ""']

		merged_blocks = base_blocks.copy()
		for b_name, b_lines in var_blocks.items():
			merged_blocks[b_name] = b_lines

		merged_statements = base_statements.copy()
		
		var_guns = [s for s in var_statements if s.strip().startswith("gun")]
		if var_guns:
			merged_statements = [s for s in merged_statements if not s.strip().startswith("gun")] + var_guns

		var_engines = [s for s in var_statements if s.strip().startswith("engine")]
		if var_engines:
			merged_statements = [s for s in merged_statements if not s.strip().startswith("engine")] + var_engines

		for stmt in merged_statements:
			if not stmt.strip().startswith("name "):
				final_lines.append(stmt)

		for b_name, b_lines in merged_blocks.items():
			final_lines.extend(b_lines)
	else:
		# Basis-Schiff: Rohdaten direkt übernehmen ohne erneutes Anhängen von Blöcken
		final_lines = []
		if lines:
			final_lines.append(lines[0])
		final_lines.append('\tname ""')

		for line in lines[1:]:
			if line.strip().startswith("name "):
				continue
			final_lines.append(line)
			
		merged_blocks, _, _ = parse_es_blocks(raw_code)

	# Attribute extrahieren
	attr_lines = merged_blocks.get("attributes", [])
	attr_dict = {}
	for line in attr_lines:
		sline = line.strip()
		if sline.startswith('"'):
			parts = sline.split('"')
			if len(parts) >= 3:
				key = parts[1]
				val = parts[2].strip()
				attr_dict[key] = val
		else:
			parts = sline.split(None, 1)
			if len(parts) == 2:
				attr_dict[parts[0]] = parts[1].strip()

	crew_val = attr_dict.get("bunks", "0")
	fuel_val = attr_dict.get("fuel capacity", "100")
	shields_val = attr_dict.get("shields", "1000")
	hull_val = attr_dict.get("hull", "1000")

	# Position von vorhandenen Schiffen im Savegame übernehmen (Fallback auf 0 0)
	position_line = "\tposition 0 0"
	if state["ships"]:
		for existing_ship in state["ships"]:
			for line in existing_ship.splitlines():
				if line.strip().startswith("position "):
					position_line = f"\t{line.strip()}"
					break
			if position_line != "\tposition 0 0":
				break

	# Runtime-Werte mit exakt 1 Tab hinzufügen
	final_lines.append(f'\tcrew {crew_val}')
	final_lines.append(f'\tfuel {fuel_val}')
	final_lines.append(f'\tshields {shields_val}')
	final_lines.append(f'\thull {hull_val}')
	final_lines.append(position_line)

	if state["system"]:
		final_lines.append(f'\tsystem "{state["system"]}"')
	if state["planet"]:
		final_lines.append(f'\tplanet "{state["planet"]}"')

	return "\n".join(final_lines)

def update_ship_preview(event=None):
	cat_key = js.document.getElementById("add-ship-category").value
	model_key = js.document.getElementById("add-ship-model").value
	preview_area = js.document.getElementById("add-ship-preview")
	add_btn = js.document.getElementById("add-ship-btn")

	if not model_key:
		preview_area.value = ""
		add_btn.disabled = True
		return

	code_preview = build_ship_syntax(model_key, cat_key)
	preview_area.value = code_preview
	add_btn.disabled = False

def add_new_ship(event):
	global current_ship_index
	cat_key = js.document.getElementById("add-ship-category").value
	model_key = js.document.getElementById("add-ship-model").value
	
	if not model_key:
		return
		
	ship_code_block = build_ship_syntax(model_key, cat_key)
	state["ships"].append(ship_code_block)
	
	render_ships_dropdown()
	new_index = len(state["ships"]) - 1
	js.document.getElementById("ship-select").value = str(new_index)
	
	current_ship_index = new_index
	js.document.getElementById("ship-code").value = ship_code_block
	js.document.getElementById("ship-details").classList.remove("hidden")
	mark_changed()

def format_filesize(size_in_bytes):
	if size_in_bytes < 1024:
		return f"{size_in_bytes} B"
	elif size_in_bytes < 1024 * 1024:
		return f"{size_in_bytes / 1024:.1f} KB"
	else:
		return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def parse_savegame(content):
	pilotname = date_str = system = planet = prev_system = prev_planet = entry_method = ""
	reputations = {}
	licenses = set()
	ships = []
	plugins = []
	conditions = []
	
	current_ship_lines = []
	active_block = None

	for line in content.splitlines():
		if line.startswith("pilot "):
			pilotname = line[6:].strip().strip('"')
			continue
		elif line.startswith("date "):
			date_str = line[5:].strip()
			continue
		elif line.startswith("system "):
			system = line[7:].strip().strip('"')
			continue
		elif line.startswith("planet "):
			planet = line[7:].strip().strip('"')
			continue
		elif line.startswith('"previous system" '):
			prev_system = line[18:].strip().strip('"')
			continue
		elif line.startswith('"previous planet" '):
			prev_planet = line[18:].strip().strip('"')
			continue
		elif line.startswith('"system entry method" '):
			entry_method = line[22:].strip().strip('"')
			continue

		if line.startswith('"reputation with"') or line.startswith("reputation"):
			active_block = "reputation"
			continue
		elif line.startswith("licenses"):
			active_block = "licenses"
			continue
		elif line.startswith("conditions"):
			active_block = "conditions"
			continue
		elif line.startswith("# What you own:"):
			active_block = "ships"
			continue
		elif line.startswith("plugins"):
			active_block = "plugins"
			continue

		if not line.startswith("\t") and not line.startswith("ship ") and line.strip() != "":
			if active_block == "ships" and current_ship_lines:
				ships.append("\n".join(current_ship_lines))
				current_ship_lines = []
			active_block = None

		if active_block == "reputation" and line.startswith("\t"):
			parts = line.strip().rsplit(" ", 1)
			if len(parts) == 2:
				try:
					clean_val = parts[1].replace(",", ".")
					reputations[parts[0].strip('"')] = float(clean_val)
				except ValueError:
					pass

		elif active_block == "licenses" and line.startswith("\t"):
			licenses.add(line.strip().strip('"'))

		elif active_block == "conditions" and line.startswith("\t"):
			conditions.append(line.strip())

		elif active_block == "plugins" and line.startswith("\t"):
			plugins.append(line.strip())

		elif active_block == "ships":
			if line.startswith("ship ") or line.startswith("\t"):
				if line.startswith("ship ") and current_ship_lines:
					ships.append("\n".join(current_ship_lines))
					current_ship_lines = []
				current_ship_lines.append(line)

	if current_ship_lines:
		ships.append("\n".join(current_ship_lines))

	credits_val = 0
	for line in content.splitlines():
		if line.startswith("\tcredits "):
			try:
				credits_val = int(line.strip().split(" ")[1])
			except (IndexError, ValueError):
				pass
			break

	return {
		"pilotname": pilotname, "date": date_str, "system": system, "planet": planet,
		"prev_system": prev_system, "prev_planet": prev_planet, "entry_method": entry_method,
		"credits": credits_val, "reputations": reputations, "licenses": licenses, 
		"ships": ships, "plugins": plugins, "conditions": conditions
	}

async def process_file(event):
	global raw_content, file_name, state, current_ship_index
	
	file_list = event.target.files
	if file_list.length == 0:
		return
	
	file = file_list.item(0)
	file_name = file.name
	raw_content = await file.text()
	
	js.document.getElementById("file-name-display").textContent = file_name
	
	state = parse_savegame(raw_content)
	current_ship_index = None

	js.document.getElementById("info-pilot").textContent = state["pilotname"] or "N/A"
	js.document.getElementById("info-date").textContent = state["date"] or "N/A"
	js.document.getElementById("info-system").textContent = state["system"] or "N/A"
	js.document.getElementById("info-planet").textContent = state["planet"] or "N/A"
	js.document.getElementById("info-prev-system").textContent = state["prev_system"] or "N/A"
	js.document.getElementById("info-prev-planet").textContent = state["prev_planet"] or "N/A"
	js.document.getElementById("info-entry-method").textContent = state["entry_method"] or "N/A"
	js.document.getElementById("info-filesize").textContent = format_filesize(file.size)

	js.document.getElementById("credits-input").value = state["credits"]

	render_licenses_grid()
	render_reputations_tables()
	render_ships_dropdown()
	render_plugins_list()
	render_conditions_view()

	js.document.getElementById("status-container").classList.remove("hidden")
	js.document.getElementById("editor-section").classList.remove("hidden")
	js.document.getElementById("download-section").classList.add("hidden")
	js.document.getElementById("save-btn").classList.add("hidden")

def get_condition_key_and_state(line):
	clean_line = line.strip()
	key_part = clean_line
	if clean_line.startswith('"'):
		parts = clean_line.split('"')
		if len(parts) >= 2:
			key_part = parts[1]
	return key_part

def extract_mission_name_from_key(key):
	suffixes = [": offered", ": done", ": failed", ": declined", ": active", ": aborted"]
	for suf in suffixes:
		if key.endswith(suf):
			return key[:-len(suf)].strip()
	return None

def analyze_mission_outcomes(script_code):
	outcomes = set(["offered"])

	for line in script_code.splitlines():
		sline = line.strip()

		if sline.startswith("decline") or sline.startswith("to decline") or sline.startswith("on decline"):
			outcomes.add("declined")

		if sline.startswith("accept") or sline.startswith("to accept") or sline.startswith("on accept"):
			outcomes.add("active")

		if sline.startswith("complete") or sline.startswith("to complete"):
			outcomes.add("done")
			outcomes.add("active")

		if sline.startswith("fail") or sline.startswith("to fail") or sline.startswith("on fail"):
			outcomes.add("failed")

		if sline.startswith("abort") or sline.startswith("to abort") or sline.startswith("on abort"):
			outcomes.add("aborted")

		if sline.startswith("on complete"):
			outcomes.add("done")
			outcomes.add("active")
			outcomes.add("failed")
			outcomes.add("declined")

	order = ["offered", "active", "done", "declined", "failed", "aborted"]
	sorted_outcomes = [o for o in order if o in outcomes]
	
	return ", ".join(sorted_outcomes)

def show_mission_detail(mission_name):
	detail_box = js.document.getElementById("mission-detail-box")
	detail_title = js.document.getElementById("mission-detail-title")
	detail_code = js.document.getElementById("mission-detail-code")
	outcome_display = js.document.getElementById("mission-outcome-display")

	if mission_name in all_global_missions:
		script_code = all_global_missions[mission_name]
		detail_title.textContent = f'Mission Script Node: "{mission_name}"'
		detail_code.value = script_code

		possible_outcomes = analyze_mission_outcomes(script_code)
		outcome_display.textContent = f"Possible mission outcome: {possible_outcomes}"

		detail_box.classList.remove("hidden")

def delete_condition(raw_line_to_delete):
	key = get_condition_key_and_state(raw_line_to_delete)
	mission_name = extract_mission_name_from_key(key)

	lines_to_remove = {raw_line_to_delete}

	if mission_name:
		offered_key = f"{mission_name}: offered"
		for line in state["conditions"]:
			if get_condition_key_and_state(line) == offered_key:
				lines_to_remove.add(line)

	state["conditions"] = [line for line in state["conditions"] if line not in lines_to_remove]
	mark_changed()
	render_conditions_view()

def render_conditions_view(event=None):
	tbody = js.document.getElementById("conditions-table-body")
	count_display = js.document.getElementById("cond-count-display")
	js.document.getElementById("mission-detail-box").classList.add("hidden")

	tbody.innerHTML = ""

	show_vanilla = js.document.getElementById("filter-vanilla").checked
	show_plugin = js.document.getElementById("filter-plugin").checked
	show_other = js.document.getElementById("filter-other").checked
	show_problematic = js.document.getElementById("filter-problematic").checked

	all_conds = state["conditions"]

	green_bases = set()
	red_bases = set()
	yellow_bases = set()

	for line in all_conds:
		key = get_condition_key_and_state(line)
		if ": active" in key:
			yellow_bases.add(key.rsplit(":", 1)[0])
		elif ": done" in key:
			green_bases.add(key.rsplit(":", 1)[0])
		elif ": failed" in key or ": declined" in key or ": aborted" in key:
			red_bases.add(key.rsplit(":", 1)[0])

	rendered_count = 0

	for line in all_conds:
		key = get_condition_key_and_state(line)
		mission_name = extract_mission_name_from_key(key)

		cond_type = "other"
		if mission_name:
			if mission_name in all_global_missions:
				cond_type = "vanilla"
			else:
				cond_type = "plugin"

		is_problematic = ": failed" in key or ": declined" in key or ": aborted" in key or (": offered" in key and key.rsplit(":", 1)[0] in red_bases)

		type_matched = False
		if cond_type == "vanilla" and show_vanilla:
			type_matched = True
		elif cond_type == "plugin" and show_plugin:
			type_matched = True
		elif cond_type == "other" and show_other:
			type_matched = True

		if not type_matched:
			continue

		if show_problematic and not is_problematic:
			continue

		rendered_count += 1

		tr = js.document.createElement("tr")
		
		td_action = js.document.createElement("td")
		btn_del = js.document.createElement("button")
		btn_del.className = "btn btn-delete"
		btn_del.textContent = "✕"
		btn_del.addEventListener("click", create_proxy(lambda e, l=line: delete_condition(l)))
		td_action.appendChild(btn_del)

		td_text = js.document.createElement("td")
		td_text.textContent = line

		td_type = js.document.createElement("td")
		td_type.style.textAlign = "right"

		span = js.document.createElement("span")
		if cond_type == "vanilla":
			span.className = "type-badge badge-vanilla"
			span.textContent = "Vanilla"
			span.addEventListener("click", create_proxy(lambda e, m=mission_name: show_mission_detail(m)))
		elif cond_type == "plugin":
			span.className = "type-badge badge-plugin"
			span.textContent = "Plugin?"
		else:
			span.className = "type-badge badge-other"
			span.textContent = "Condition"

		td_type.appendChild(span)

		base_name = key.rsplit(":", 1)[0] if ":" in key else key
		if ": active" in key or (": offered" in key and base_name in yellow_bases):
			tr.className = "cond-row-yellow"
		elif ": done" in key or (": offered" in key and base_name in green_bases):
			tr.className = "cond-row-green"
		elif is_problematic:
			tr.className = "cond-row-red"
		else:
			tr.className = "cond-row-blue"

		tr.appendChild(td_action)
		tr.appendChild(td_text)
		tr.appendChild(td_type)
		tbody.appendChild(tr)

	count_display.textContent = f"{rendered_count} / {len(all_conds)} Conditions"

def render_licenses_grid():
	container = js.document.getElementById("license-checkbox-container")
	container.innerHTML = ""

	for lic in ALL_LICENSES:
		label_elem = js.document.createElement("label")
		label_elem.className = "license-checkbox"

		chk = js.document.createElement("input")
		chk.type = "checkbox"
		chk.value = lic
		chk.checked = lic in state["licenses"]
		chk.addEventListener("change", create_proxy(on_license_toggle))

		span_elem = js.document.createElement("span")
		span_elem.textContent = lic

		label_elem.appendChild(chk)
		label_elem.appendChild(span_elem)
		container.appendChild(label_elem)

def on_license_toggle(event):
	lic_name = event.target.value
	if event.target.checked:
		state["licenses"].add(lic_name)
	else:
		state["licenses"].discard(lic_name)
	mark_changed()

def render_reputations_tables():
	t1 = js.document.getElementById("reputations-table-1")
	t2 = js.document.getElementById("reputations-table-2")
	t3 = js.document.getElementById("reputations-table-3")
	t4 = js.document.getElementById("reputations-table-4")
	t1.innerHTML = ""
	t2.innerHTML = ""
	t3.innerHTML = ""
	t4.innerHTML = ""
	
	items = list(state["reputations"].items())
	total = len(items)
	col_size = (total + 3) // 4
	
	for idx, (faction, val) in enumerate(items):
		tr = js.document.createElement("tr")
		
		td_faction = js.document.createElement("td")
		td_faction.className = "faction-cell"
		td_faction.textContent = faction
		
		td_val = js.document.createElement("td")
		td_val.className = "value-cell"
		inp = js.document.createElement("input")
		inp.type = "number"
		inp.step = "any"
		inp.setAttribute("lang", "en-US")
		
		if isinstance(val, float) and val.is_integer():
			inp.value = str(int(val))
		else:
			inp.value = str(val).replace(",", ".")
			
		inp.dataset.faction = faction
		inp.addEventListener("change", create_proxy(on_reputation_change))
		
		td_val.appendChild(inp)
		tr.appendChild(td_faction)
		tr.appendChild(td_val)
		
		if idx < col_size:
			t1.appendChild(tr)
		elif idx < col_size * 2:
			t2.appendChild(tr)
		elif idx < col_size * 3:
			t3.appendChild(tr)
		else:
			t4.appendChild(tr)

def render_plugins_list():
	container = js.document.getElementById("plugins-list-container")
	container.innerHTML = ""
	
	if not state["plugins"]:
		li = js.document.createElement("li")
		li.textContent = "No active plugins found in this savegame."
		li.style.listStyleType = "none"
		container.appendChild(li)
		return

	for plugin in state["plugins"]:
		li = js.document.createElement("li")
		li.textContent = plugin
		container.appendChild(li)

def render_ships_dropdown():
	ship_select = js.document.getElementById("ship-select")
	ship_select.innerHTML = '<option value="">-- Select owned ship --</option>'
	
	for idx, ship_block in enumerate(state["ships"]):
		first_line = ship_block.splitlines()[0] if ship_block.splitlines() else "ship"
		ship_label = first_line.replace('ship ', '').replace('"', '')
		
		for s_line in ship_block.splitlines():
			if s_line.startswith('\tname '):
				parts = s_line.strip().split(' ', 1)
				if len(parts) > 1:
					custom_name = parts[1].strip('"')
					if custom_name:
						ship_label = f"{ship_label} ({custom_name})"
				break
		
		option = js.document.createElement("option")
		option.value = str(idx)
		option.textContent = f"{idx + 1}. {ship_label}"
		ship_select.appendChild(option)

def on_reputation_change(event):
	faction = event.target.dataset.faction
	val_str = event.target.value.replace(",", ".")
	try:
		state["reputations"][faction] = float(val_str) if "." in val_str else int(val_str)
		mark_changed()
	except ValueError:
		pass

def on_credits_change(event):
	mark_changed()

def save_current_ship_code_to_state():
	global current_ship_index
	if current_ship_index is not None and current_ship_index < len(state["ships"]):
		code_value = js.document.getElementById("ship-code").value
		state["ships"][current_ship_index] = code_value

def on_ship_selected(event):
	global current_ship_index
	save_current_ship_code_to_state()

	selected_value = event.target.value
	ship_details = js.document.getElementById("ship-details")
	
	if selected_value != "":
		current_ship_index = int(selected_value)
		js.document.getElementById("ship-code").value = state["ships"][current_ship_index]
		ship_details.classList.remove("hidden")
	else:
		current_ship_index = None
		ship_details.classList.add("hidden")

def on_ship_code_input(event):
	save_current_ship_code_to_state()
	mark_changed()

def insert_tab_at_cursor(event):
	textarea = js.document.getElementById("ship-code")
	start = textarea.selectionStart
	end = textarea.selectionEnd

	textarea.value = textarea.value[:start] + "\t" + textarea.value[end:]
	textarea.selectionStart = textarea.selectionEnd = start + 1
	textarea.focus()
	save_current_ship_code_to_state()
	mark_changed()

def switch_tab(section_id):
	save_current_ship_code_to_state()
	
	js.document.getElementById("section-ships").classList.add("hidden")
	js.document.getElementById("section-reputations").classList.add("hidden")
	js.document.getElementById("section-licenses").classList.add("hidden")
	js.document.getElementById("section-conditions").classList.add("hidden")
	js.document.getElementById("section-plugins").classList.add("hidden")
	
	js.document.getElementById(section_id).classList.remove("hidden")

def apply_changes(event):
	global raw_content, file_name, state
	
	save_current_ship_code_to_state()
	state["credits"] = js.document.getElementById("credits-input").value

	lines = raw_content.splitlines()
	updated_lines = []
	skip_block = False

	for line in lines:
		if line.startswith("\tcredits "):
			updated_lines.append(f'\tcredits {state["credits"]}')
			continue

		if line.startswith("licenses"):
			skip_block = True
			updated_lines.append("licenses")
			for lic in sorted(state["licenses"]):
				updated_lines.append(f'\t"{lic}"')
			continue

		if line.startswith('"reputation with"') or line.startswith("reputation"):
			skip_block = True
			updated_lines.append('"reputation with"')
			for faction, value in state["reputations"].items():
				val_str = str(value).replace(",", ".")
				updated_lines.append(f'\t"{faction}" {val_str}')
			continue

		if line.startswith("conditions"):
			skip_block = True
			updated_lines.append("conditions")
			for cond_line in state["conditions"]:
				updated_lines.append(f'\t{cond_line}')
			continue

		if line.startswith("# What you own:"):
			skip_block = True
			updated_lines.append("# What you own:")
			for ship_block in state["ships"]:
				updated_lines.append(ship_block)
			continue

		if skip_block and not line.startswith("\t") and not line.startswith("ship ") and line.strip() != "":
			skip_block = False

		if not skip_block:
			updated_lines.append(line)

	updated_content = "\n".join(updated_lines)

	blob = js.Blob.new([updated_content], {type: "text/plain"})
	url = js.URL.createObjectURL(blob)
	
	download_link = js.document.getElementById("download-link")
	download_link.href = url
	download_link.download = file_name
	
	js.document.getElementById("download-section").classList.remove("hidden")

def handle_textarea_tab(event):
	if event.key == "Tab":
		event.preventDefault()
		textarea = event.target
		start = textarea.selectionStart
		end = textarea.selectionEnd

		textarea.value = textarea.value[:start] + "\t" + textarea.value[end:]
		textarea.selectionStart = textarea.selectionEnd = start + 1

# Event Listener Binding
js.document.getElementById("file-input").addEventListener("change", create_proxy(process_file))
js.document.getElementById("credits-input").addEventListener("input", create_proxy(on_credits_change))
js.document.getElementById("ship-select").addEventListener("change", create_proxy(on_ship_selected))
js.document.getElementById("ship-code").addEventListener("input", create_proxy(on_ship_code_input))
js.document.getElementById("ship-code").addEventListener("keydown", create_proxy(handle_textarea_tab))
js.document.getElementById("insert-tab-btn").addEventListener("click", create_proxy(insert_tab_at_cursor))

js.document.getElementById("add-ship-category").addEventListener("change", create_proxy(on_category_changed))
js.document.getElementById("add-ship-model").addEventListener("change", create_proxy(update_ship_preview))
js.document.getElementById("add-ship-btn").addEventListener("click", create_proxy(add_new_ship))

# Checkbox-Filter Event Bindings
js.document.getElementById("filter-vanilla").addEventListener("change", create_proxy(render_conditions_view))
js.document.getElementById("filter-plugin").addEventListener("change", create_proxy(render_conditions_view))
js.document.getElementById("filter-other").addEventListener("change", create_proxy(render_conditions_view))
js.document.getElementById("filter-problematic").addEventListener("change", create_proxy(render_conditions_view))

js.document.getElementById("show-ships-btn").addEventListener("click", create_proxy(lambda e: switch_tab("section-ships")))
js.document.getElementById("show-rep-btn").addEventListener("click", create_proxy(lambda e: switch_tab("section-reputations")))
js.document.getElementById("show-lic-btn").addEventListener("click", create_proxy(lambda e: switch_tab("section-licenses")))
js.document.getElementById("show-cond-btn").addEventListener("click", create_proxy(lambda e: switch_tab("section-conditions")))
js.document.getElementById("show-plug-btn").addEventListener("click", create_proxy(lambda e: switch_tab("section-plugins")))

js.document.getElementById("save-btn").addEventListener("click", create_proxy(apply_changes))

# JSON laden
asyncio.ensure_future(load_remote_ship_data())