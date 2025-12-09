import flet as ft
import shutil
import os
import time
from services.pageant_service import PageantService
from services.event_service import EventService
from services.contestant_service import ContestantService
from services.admin_service import AdminService
from services.export_service import ExportService
from core.database import SessionLocal
from models.all_models import Segment, Criteria, Event
from components.dialogs import show_about_dialog, show_contact_dialog
import datetime
import os

def PageantConfigView(page: ft.Page, event_id: int):
    # Services
    pageant_service = PageantService()
    event_service = EventService()
    contestant_service = ContestantService()
    admin_service = AdminService()
    export_service = ExportService()

    # --- FETCH EVENT DETAILS FOR HEADER ---
    db = SessionLocal()
    event_obj = db.query(Event).get(event_id)
    event_name = event_obj.name if event_obj else "Pageant Event"
    db.close()

    # --- PERMISSION CHECK ---
    user_role = page.session.get("user_role")
    is_read_only = (user_role == "AdminViewer")

    # --- STATE VARIABLES ---
    # Config Tab State
    editing_segment_id = None 
    editing_criteria_id = None 
    selected_segment_id = None
    pending_action_seg_id = None 
    
    # Contestant Tab State
    uploaded_file_path = None
    editing_contestant_id = None
    
    # Export State
    pending_export_type = None 
    selected_export_scope = "overall" # Default to overall

    # --- HEADER CONSTRUCTION ---
    header_logo = ft.Container(
        width=40, height=40, border_radius=50, bgcolor="transparent",
        border=ft.border.all(2, "black"), padding=5,
        content=ft.Image(src="hammer.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.GAVEL, color="black"))
    )

    header = ft.Container(
        height=70, padding=ft.padding.symmetric(horizontal=20), bgcolor="#80C1FF",
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_300),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_color="black", on_click=lambda e: page.go("/admin")),
                    header_logo, 
                    # Indicate Auditor View in Title
                    ft.Text(f"Config: {event_name}" if not is_read_only else f"Auditing: {event_name}", size=20, weight="bold", color="black", overflow=ft.TextOverflow.ELLIPSIS)
                ]),
                ft.Row(spacing=5, controls=[
                    ft.TextButton("LEADERBOARD", icon=ft.Icons.EMOJI_EVENTS, style=ft.ButtonStyle(color="black"), on_click=lambda e: page.go("/leaderboard")),
                    ft.TextButton("ABOUT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_about_dialog(page)),
                    ft.TextButton("CONTACT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_contact_dialog(page)),
                ])
            ]
        )
    )

    # --- UI WRAPPERS FOR TABS (Styled) ---
    config_tab_content = ft.Column(spacing=15, scroll="adaptive", expand=True)
    contestant_tab_content = ft.Column(spacing=15, scroll="adaptive", expand=True)
    judges_tab_content = ft.Column(spacing=15, scroll="adaptive", expand=True)
    scores_tab_content = ft.Column(spacing=15, scroll="adaptive", expand=True)

    # =================================================================================================
    # TAB 1: CONFIGURATION
    # =================================================================================================
    
    # --- UI CONTROLS ---
    p_seg_name = ft.TextField(label="Segment Name", width=280, dense=True)
    p_seg_weight = ft.TextField(label="Weight (%)", suffix_text="%", keyboard_type=ft.KeyboardType.NUMBER, width=280, dense=True)
    p_crit_name = ft.TextField(label="Criteria Name", width=280, dense=True)
    p_crit_weight = ft.TextField(label="Weight (%)", suffix_text="%", keyboard_type=ft.KeyboardType.NUMBER, width=280, dense=True)
    p_crit_max = ft.TextField(label="Max Score", value="100", keyboard_type=ft.KeyboardType.NUMBER, width=280, dense=True) 
    
    p_is_final = ft.Checkbox(label="Is Final Round?", value=False)
    p_qualifiers = ft.TextField(label="Qualifiers Count", value="5", width=280, visible=False, keyboard_type=ft.KeyboardType.NUMBER, dense=True)

    def on_final_check(e):
        p_qualifiers.visible = p_is_final.value
        p_seg_weight.disabled = p_is_final.value 
        if p_is_final.value: p_seg_weight.value = "100" 
        page.update()
    p_is_final.on_change = on_final_check

    # --- REFRESH LOGIC ---
    def refresh_config_tab():
        config_tab_content.controls.clear()
        
        db = SessionLocal()
        segments = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
        final_round_is_active = any(s.is_active and s.is_final for s in segments)

        # Header Row
        # Hide Action Buttons if Read Only
        action_buttons = ft.Row([
            ft.OutlinedButton("Deactivate All", icon=ft.Icons.STOP_CIRCLE, style=ft.ButtonStyle(color="red"), on_click=lambda e: request_toggle_status(None)),
            ft.ElevatedButton("Add Segment", icon=ft.Icons.ADD, on_click=open_add_seg_dialog, bgcolor="#64AEFF", color="white")
        ]) if not is_read_only else ft.Container()

        config_tab_content.controls.append(ft.Row([
            ft.Text("Pageant Rounds", size=24, weight="bold"),
            action_buttons
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        current_total_weight = 0.0

        for seg in segments:
            if not seg.is_final:
                current_total_weight += seg.percentage_weight
            
            criterias = db.query(Criteria).filter(Criteria.segment_id == seg.id).all()
            crit_list = ft.Column(spacing=0)
            
            for c in criterias:
                # Criteria Edit Button
                crit_edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_size=16, icon_color="grey", tooltip="Edit Criteria", data=c, on_click=open_edit_crit_dialog) if not is_read_only else ft.Container()
                
                crit_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Icon(ft.Icons.SUBDIRECTORY_ARROW_RIGHT, size=16, color="grey"),
                                ft.Text(f"{c.name}", weight="w500", size=14),
                            ]),
                            ft.Row([
                                ft.Text(f"{int(c.weight * 100)}%", size=12, color="grey"),
                                ft.Text(f"/ {c.max_score} pts", size=12, color="blue"),
                                crit_edit_btn
                            ], spacing=10)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(left=40, right=10, top=5, bottom=5),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "#F0F0F0"))
                    )
                )

            # STATUS LOGIC
            if seg.is_active:
                status_color = ft.Colors.GREEN_50
                status_text = "ACTIVE"
                status_icon = ft.Icons.RADIO_BUTTON_CHECKED
                border_side = ft.border.all(2, ft.Colors.GREEN)
                opacity = 1.0
                is_disabled = False 
            else:
                status_color = "white"
                status_text = "INACTIVE"
                status_icon = ft.Icons.RADIO_BUTTON_UNCHECKED
                border_side = ft.border.all(1, "#E0E0E0")
                
                if final_round_is_active:
                    opacity = 0.6 
                    is_disabled = True 
                else:
                    opacity = 1.0
                    is_disabled = False
            
            # Force disable status toggle if read only
            if is_read_only: is_disabled = True

            if seg.is_final:
                card_bg = ft.Colors.AMBER_50 if seg.is_active else "white"
                badge = ft.Container(content=ft.Text(f"FINAL (Top {seg.qualifier_limit})", color="black", size=10, weight="bold"), bgcolor=ft.Colors.AMBER_300, padding=5, border_radius=5)
            else:
                card_bg = status_color
                badge = ft.Container(content=ft.Text(f"{int(seg.percentage_weight * 100)}%", size=10, color="white", weight="bold"), bgcolor="#64AEFF", padding=5, border_radius=5)

            reveal_icon = ft.Icons.VISIBILITY if getattr(seg, 'is_revealed', False) else ft.Icons.VISIBILITY_OFF
            reveal_color = ft.Colors.BLUE if getattr(seg, 'is_revealed', False) else ft.Colors.GREY
            reveal_tooltip = "Visible on Leaderboard" if getattr(seg, 'is_revealed', False) else "Hidden from Leaderboard"
            
            # Action Buttons Row
            if not is_read_only:
                actions_row = ft.Row([
                    ft.IconButton(
                        icon=reveal_icon, 
                        icon_color=reveal_color, 
                        tooltip=reveal_tooltip,
                        data=seg.id, 
                        on_click=lambda e: toggle_reveal(e.control.data)
                    ),
                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Edit", icon_color="blue", data=seg, on_click=open_edit_seg_dialog),
                    ft.IconButton(icon=ft.Icons.ADD_CIRCLE, tooltip="Add Criteria", icon_color="green", data=seg.id, on_click=open_add_crit_dialog)
                ])
            else:
                actions_row = ft.Container() # Empty for auditors

            # New Modern Card Layout
            card_content = ft.Column([
                ft.Container(
                    padding=15,
                    bgcolor=card_bg,
                    content=ft.Row([
                        ft.Row([
                            ft.IconButton(
                                icon=status_icon, 
                                icon_color="green" if seg.is_active else "grey",
                                data=seg.id,
                                disabled=is_disabled,
                                tooltip="Activate Round (Disabled)" if is_read_only else "Activate Round",
                                on_click=lambda e, s=seg: request_final_activation(s.id) if s.is_final else request_toggle_status(s.id)
                            ),
                            ft.Text(f"{seg.name}", size=16, weight="bold"),
                            badge,
                        ], spacing=10),
                        
                        actions_row
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ),
                ft.Divider(height=1, color="#E0E0E0"),
                ft.Container(
                    content=crit_list if criterias else ft.Text("No criteria added yet.", italic=True, color="grey", size=12),
                    padding=10
                )
            ], spacing=0)

            container = ft.Container(
                content=card_content,
                bgcolor="white",
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                border=border_side,
                opacity=opacity,
                margin=ft.margin.only(bottom=10)
            )
            config_tab_content.controls.append(container)
        
        if current_total_weight > 1.0001:
            config_tab_content.controls.append(ft.Container(content=ft.Text(f"⚠️ Prelim Weight is {int(current_total_weight*100)}%. It should be 100%.", color="red", weight="bold"), bgcolor=ft.Colors.RED_50, padding=10, border_radius=5))
        elif current_total_weight < 0.999:
            config_tab_content.controls.append(ft.Container(content=ft.Text(f"ℹ️ Prelim Weight is {int(current_total_weight*100)}%. Add more segments to reach 100%.", color="blue", weight="bold"), bgcolor=ft.Colors.BLUE_50, padding=10, border_radius=5))
        else:
             config_tab_content.controls.append(ft.Container(content=ft.Text("✅ Prelim Weight is perfect (100%).", color="green", weight="bold"), bgcolor=ft.Colors.GREEN_50, padding=10, border_radius=5))

        db.close()
        page.update()

    # ... (Keep existing helpers: toggle_reveal, confirm/strict dialogs, request_toggle_status, execute_toggle, final_activation logic, save handlers) ...
    # They are safe to keep because the buttons triggering them are hidden for Read Only users.

    def toggle_reveal(seg_id):
        success, msg = event_service.toggle_segment_reveal(seg_id)
        if success:
            page.open(ft.SnackBar(ft.Text(msg), bgcolor="green"))
            refresh_config_tab()
        else:
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))

    # --- SAFETY DIALOGS ---
    def confirm_simple_action(e):
        execute_toggle(pending_action_seg_id)
        page.close(simple_dialog)

    simple_dialog = ft.AlertDialog(
        title=ft.Text("Confirm Activation"),
        content=ft.Text("Are you sure you want to activate this segment?"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(simple_dialog)),
            ft.TextButton("Yes, Activate", on_click=confirm_simple_action),
        ]
    )

    confirm_input = ft.TextField(label="Type CONFIRM", border_color="red", dense=True)
    confirm_btn = ft.ElevatedButton("Proceed", bgcolor="red", color="white", disabled=True)

    def validate_strict_input(e):
        text = confirm_input.value.strip().upper()
        is_valid = (text == "CONFIRM")
        confirm_btn.disabled = not is_valid
        confirm_btn.bgcolor = ft.Colors.RED if is_valid else ft.Colors.GREY
        confirm_btn.update()

    def confirm_strict_action(e):
        execute_toggle(pending_action_seg_id)
        page.close(strict_dialog)
        confirm_input.value = ""

    confirm_btn.on_click = confirm_strict_action
    confirm_input.on_change = validate_strict_input

    strict_dialog = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.Icons.WARNING, color="red"), ft.Text("Warning: Disruptive Action")]),
        content=ft.Column([
            ft.Text("You are about to deactivate or swap the active segment."),
            ft.Text("Warning: The judge might not be finished plotting scores.", color="red", weight="bold"),
            ft.Container(height=10),
            ft.Text("Type 'CONFIRM' to proceed:", size=12, weight="bold"),
            confirm_input
        ], tight=True, width=400),
        actions=[ft.TextButton("Cancel", on_click=lambda e: page.close(strict_dialog)), confirm_btn]
    )

    def request_toggle_status(seg_id):
        nonlocal pending_action_seg_id
        pending_action_seg_id = seg_id
        active_seg = event_service.get_active_segment(event_id)
        
        db = SessionLocal()
        all_segs = db.query(Segment).filter(Segment.event_id == event_id).all()
        final_is_active = any(s.is_active and s.is_final for s in all_segs)
        active_obj = next((s for s in all_segs if s.is_active), None)
        db.close()

        if final_is_active and seg_id is not None:
             if active_obj and active_obj.id == seg_id: pass
             else:
                 page.open(ft.SnackBar(ft.Text("Cannot switch segments while Final Round is active!"), bgcolor="red"))
                 return

        if seg_id is None: 
            if not active_seg: return
            page.open(strict_dialog)
            return
        if active_seg and active_seg.id != seg_id: 
            page.open(strict_dialog)
            return
        if active_seg and active_seg.id == seg_id: 
             page.open(strict_dialog)
             return
        page.open(simple_dialog) 

    def execute_toggle(seg_id):
        success, msg = event_service.set_active_segment(event_id, seg_id)
        if success:
            page.open(ft.SnackBar(ft.Text(msg), bgcolor="green"))
            refresh_config_tab()
        else:
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))

    # --- FINAL ROUND DIALOG ---
    final_confirm_input = ft.TextField(label="Type CONFIRM", border_color="red", dense=True)
    final_confirm_btn = ft.ElevatedButton("ACTIVATE FINAL ROUND", bgcolor="grey", color="white", disabled=True)

    def validate_final_input(e):
        final_confirm_btn.disabled = (final_confirm_input.value != "CONFIRM")
        final_confirm_btn.bgcolor = "red" if final_confirm_input.value == "CONFIRM" else "grey"
        final_confirm_btn.update()

    def request_final_activation(seg_id):
        db = SessionLocal()
        seg = db.query(Segment).get(seg_id)
        limit = seg.qualifier_limit
        db.close()

        rankings = pageant_service.get_preliminary_rankings(event_id)
        qualifiers_controls = []
        eliminated_controls = []
        
        def build_list(rank_list, title):
            if rank_list:
                qualifiers_controls.append(ft.Text(f"--- {title} ---", color="blue", weight="bold"))
                eliminated_controls.append(ft.Text(f"--- {title} ---", color="blue", weight="bold"))
                for i, r in enumerate(rank_list):
                    rank = i + 1
                    line = f"#{rank} {r['contestant'].name} ({r['score']}%)"
                    if i < limit:
                        qualifiers_controls.append(ft.Text(line, weight="bold", color="green", size=16))
                    else:
                        eliminated_controls.append(ft.Text(line, color="grey", size=14))

        build_list(rankings['Male'], "MALE")
        build_list(rankings['Female'], "FEMALE")

        if not qualifiers_controls:
            qualifiers_controls.append(ft.Text("No scores recorded yet.", italic=True, color="orange"))

        final_confirm_input.value = ""
        final_confirm_input.on_change = validate_final_input
        final_confirm_btn.disabled = True
        final_confirm_btn.bgcolor = "grey"

        dlg = ft.AlertDialog(
            title=ft.Text("FINAL ROUND ACTIVATION"),
            content=ft.Column([
                ft.Text(f"Activating this will ELIMINATE candidates below Rank {limit}.", color="red", weight="bold"),
                ft.Divider(),
                ft.Text(f"QUALIFIERS (Top {limit}):", weight="bold"),
                ft.Column(controls=qualifiers_controls, spacing=2), 
                ft.Divider(),
                ft.Text("ELIMINATED:", weight="bold"),
                ft.Column(controls=eliminated_controls, spacing=2),
                ft.Divider(),
                ft.Text("Type 'CONFIRM' to proceed:", size=12, weight="bold"),
                final_confirm_input
            ], scroll="adaptive", height=400, width=500),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(dlg)),
                final_confirm_btn
            ]
        )
        final_confirm_btn.on_click = lambda e: execute_final_activation(seg_id, limit, dlg)
        page.open(dlg)

    def execute_final_activation(seg_id, limit, dlg):
        success, q, e = pageant_service.activate_final_round(event_id, seg_id, limit)
        page.close(dlg)
        if success:
            page.open(ft.SnackBar(ft.Text(f"Final Round Active! {len(q)} Qualified."), bgcolor="green"))
            refresh_config_tab()
        else:
            page.open(ft.SnackBar(ft.Text("Error activating round."), bgcolor="red"))

    # --- SAVE HANDLERS ---
    def save_segment(e):
        try:
            if not p_is_final.value:
                raw_val = float(p_seg_weight.value)
                w = raw_val / 100.0 if raw_val > 1.0 else raw_val
            else:
                w = 0 
            limit = int(p_qualifiers.value) if p_is_final.value else 0

            if editing_segment_id:
                success, msg = event_service.update_segment(editing_segment_id, p_seg_name.value, w, p_is_final.value, limit)
            else:
                success, msg = event_service.add_segment(event_id, p_seg_name.value, w, 1, p_is_final.value, limit)

            if success:
                page.open(ft.SnackBar(ft.Text("Saved!"), bgcolor="green"))
                page.close(seg_dialog)
                refresh_config_tab()
            else:
                page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
        except ValueError:
             page.open(ft.SnackBar(ft.Text("Invalid Input"), bgcolor="red"))

    def save_criteria(e):
        try:
            raw_val = float(p_crit_weight.value)
            w = raw_val / 100.0 if raw_val > 1.0 else raw_val
            
            max_s = int(p_crit_max.value) if p_crit_max.value else 100

            if editing_criteria_id:
                success, msg = pageant_service.update_criteria(editing_criteria_id, p_crit_name.value, w, max_s)
            else:
                success, msg = pageant_service.add_criteria(selected_segment_id, p_crit_name.value, w, max_s)

            if success:
                page.open(ft.SnackBar(ft.Text("Saved!"), bgcolor="green"))
                page.close(crit_dialog)
                refresh_config_tab()
            else:
                page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
        except ValueError:
             page.open(ft.SnackBar(ft.Text("Invalid Input"), bgcolor="red"))

    seg_dialog = ft.AlertDialog(
        title=ft.Text("Segment Details"),
        content=ft.Column([p_seg_name, p_is_final, p_qualifiers, p_seg_weight], height=250, width=300, tight=True),
        actions=[ft.TextButton("Save", on_click=save_segment)]
    )
    
    crit_dialog = ft.AlertDialog(
        title=ft.Text("Criteria Details"),
        content=ft.Column([p_crit_name, p_crit_weight, p_crit_max], height=250, width=300, tight=True),
        actions=[ft.TextButton("Save", on_click=save_criteria)]
    )

    def open_add_seg_dialog(e):
        nonlocal editing_segment_id
        editing_segment_id = None 
        p_seg_name.value = ""
        p_seg_weight.value = ""
        p_is_final.value = False
        on_final_check(None)
        seg_dialog.title.value = "Add Segment"
        page.open(seg_dialog)

    def open_edit_seg_dialog(e):
        nonlocal editing_segment_id
        seg_data = e.control.data
        editing_segment_id = seg_data.id 
        p_seg_name.value = seg_data.name
        p_seg_weight.value = str(int(seg_data.percentage_weight * 100))
        p_is_final.value = seg_data.is_final
        p_qualifiers.value = str(seg_data.qualifier_limit)
        on_final_check(None)
        seg_dialog.title.value = "Edit Segment"
        page.open(seg_dialog)

    def open_add_crit_dialog(e):
        nonlocal selected_segment_id, editing_criteria_id
        selected_segment_id = e.control.data
        editing_criteria_id = None 
        p_crit_name.value = ""
        p_crit_weight.value = ""
        p_crit_max.value = "100" # Default
        crit_dialog.title.value = "Add Criteria"
        page.open(crit_dialog)

    def open_edit_crit_dialog(e):
        nonlocal editing_criteria_id
        crit_data = e.control.data
        editing_criteria_id = crit_data.id 
        p_crit_name.value = crit_data.name
        p_crit_weight.value = str(int(crit_data.weight * 100))
        p_crit_max.value = str(crit_data.max_score) # Load existing max
        crit_dialog.title.value = "Edit Criteria"
        page.open(crit_dialog)

    # =================================================================================================
    # TAB 2: CONTESTANTS (With Male/Female Separation)
    # =================================================================================================
    c_number = ft.TextField(label="#", width=80, keyboard_type=ft.KeyboardType.NUMBER, dense=True)
    c_name = ft.TextField(label="Name", width=250, dense=True)
    c_gender = ft.Dropdown(label="Gender", width=250, dense=True, options=[ft.dropdown.Option("Female"), ft.dropdown.Option("Male")], value="Female")
    img_preview = ft.Image(width=100, height=100, fit=ft.ImageFit.COVER, visible=False, border_radius=10)
    
    # File Picker Logic
    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal uploaded_file_path
        if e.files:
            try:
                os.makedirs("assets/uploads", exist_ok=True)
                file_obj = e.files[0]
                safe_name = f"img_{int(time.time())}_{file_obj.name}"
                shutil.copy(file_obj.path, os.path.join("assets/uploads", safe_name))
                uploaded_file_path = f"uploads/{safe_name}"
                img_preview.src = uploaded_file_path
                img_preview.visible = True
                img_preview.update()
            except Exception as ex: page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red"))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    upload_btn = ft.ElevatedButton("Photo", icon=ft.Icons.UPLOAD, on_click=lambda _: file_picker.pick_files(allow_multiple=False))

    def save_contestant(e):
        if not c_number.value or not c_name.value: page.open(ft.SnackBar(ft.Text("Missing info"), bgcolor="red")); return
        try:
            num = int(c_number.value)
            if editing_contestant_id: success, msg = contestant_service.update_contestant(editing_contestant_id, num, c_name.value, c_gender.value, uploaded_file_path)
            else: success, msg = contestant_service.add_contestant(event_id, num, c_name.value, c_gender.value, uploaded_file_path)
            
            if success: page.open(ft.SnackBar(ft.Text("Saved!"), bgcolor="green")); page.close(contestant_dialog); refresh_contestant_tab()
            else: page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
        except: page.open(ft.SnackBar(ft.Text("Invalid Number"), bgcolor="red"))

    contestant_dialog = ft.AlertDialog(title=ft.Text("Contestant"), content=ft.Column([ft.Row([c_number, c_gender]), c_name, ft.Row([upload_btn, img_preview])], height=250, width=300), actions=[ft.TextButton("Save", on_click=save_contestant)])
    
    def open_add_c_dialog(e): nonlocal editing_contestant_id, uploaded_file_path; editing_contestant_id=None; uploaded_file_path=None; c_number.value=""; c_name.value=""; img_preview.visible=False; page.open(contestant_dialog)
    def open_edit_c_dialog(e): nonlocal editing_contestant_id, uploaded_file_path; d=e.control.data; editing_contestant_id=d.id; uploaded_file_path=d.image_path; c_number.value=str(d.candidate_number); c_name.value=d.name; c_gender.value=d.gender; img_preview.src=d.image_path if d.image_path else ""; img_preview.visible=bool(d.image_path); page.open(contestant_dialog)
    def delete_contestant(e): contestant_service.delete_contestant(e.control.data); refresh_contestant_tab()

    def refresh_contestant_tab():
        contestant_tab_content.controls.clear()
        contestants = contestant_service.get_contestants(event_id)
        
        # Header Row
        # Hide Add Button if Read Only
        add_candidate_btn = ft.ElevatedButton("Add Candidate", icon=ft.Icons.ADD, on_click=open_add_c_dialog, bgcolor="#64AEFF", color="white") if not is_read_only else ft.Container()
        
        contestant_tab_content.controls.append(ft.Row([
            ft.Text("Pageant Candidates", size=24, weight="bold"),
            add_candidate_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        def build_list(gender, icon, color):
            items = [c for c in contestants if c.gender == gender]
            title_color = "#64AEFF" if gender == "Male" else "#FF64AE"
            
            # List items
            list_items = []
            for c in items:
                avatar = ft.CircleAvatar(
                    foreground_image_src=c.image_path if c.image_path else "",
                    content=ft.Text(c.name[0]) if not c.image_path else None,
                    bgcolor=color,
                    radius=20
                )
                
                # Actions Row
                if not is_read_only:
                    actions = ft.Row([
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color="blue", icon_size=18, data=c, on_click=open_edit_c_dialog),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", icon_size=18, data=c.id, on_click=delete_contestant)
                    ])
                else:
                    actions = ft.Container()

                list_items.append(ft.Container(
                    padding=10, 
                    bgcolor="white", 
                    border_radius=10,
                    margin=ft.margin.only(bottom=5),
                    shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK12),
                    border=ft.border.all(1, "#F0F0F0"),
                    content=ft.Row([
                        ft.Row([
                            ft.Container(content=ft.Text(f"#{c.candidate_number}", color="white", weight="bold", size=12), bgcolor="black", padding=8, border_radius=5),
                            avatar,
                            ft.Text(c.name, weight="bold", size=14)
                        ]),
                        actions
                    ], alignment="spaceBetween")
                ))
            
            # Column Wrapper for Gender
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{gender.upper()} CANDIDATES", weight="bold", color=title_color, size=16),
                    ft.Divider(color=title_color, height=2),
                    ft.Column(list_items, spacing=5)
                ]),
                expand=True,
                padding=10,
                bgcolor="#F9FAFB",
                border_radius=10
            )

        contestant_tab_content.controls.append(ft.Row([
            build_list("Male", ft.Colors.BLUE_100, "blue"), 
            ft.VerticalDivider(width=20, color="transparent"),
            build_list("Female", ft.Colors.PINK_100, "pink")
        ], expand=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START))
        
        page.update()

    # =================================================================================================
    # TAB 3: JUDGES
    # =================================================================================================
    j_select = ft.Dropdown(label="Select Judge", width=300, dense=True)
    j_is_chairman = ft.Checkbox(label="Is Chairman?", value=False)
    
    def save_judge(e):
        if not j_select.value: return
        success, msg = event_service.assign_judge(event_id, int(j_select.value), j_is_chairman.value)
        if success: page.open(ft.SnackBar(ft.Text(msg), bgcolor="green")); page.close(judge_dialog); refresh_judges_tab()
        else: page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))

    judge_dialog = ft.AlertDialog(title=ft.Text("Assign Judge"), content=ft.Column([j_select, j_is_chairman], height=150, width=300), actions=[ft.TextButton("Assign", on_click=save_judge)])
    
    def open_judge_dialog(e):
        users = admin_service.get_all_judges()
        j_select.options = [ft.dropdown.Option(key=str(u.id), text=u.name) for u in users]
        page.open(judge_dialog)

    def remove_judge(e): event_service.remove_judge(e.control.data); refresh_judges_tab()

    def refresh_judges_tab():
        judges_tab_content.controls.clear()
        
        # Header
        assign_btn = ft.ElevatedButton("Assign Judge", icon=ft.Icons.ADD, on_click=open_judge_dialog, bgcolor="#64AEFF", color="white") if not is_read_only else ft.Container()

        judges_tab_content.controls.append(ft.Row([
            ft.Text("Panel of Judges", size=24, weight="bold"), 
            assign_btn
        ], alignment="spaceBetween"))
        
        assigned = event_service.get_assigned_judges(event_id)
        
        cards = []
        for aj in assigned:
            role_col = "orange" if aj.is_chairman else "#64AEFF"
            
            remove_icon = ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", data=aj.id, on_click=remove_judge) if not is_read_only else ft.Container()

            cards.append(ft.Container(
                padding=20, 
                bgcolor="white", 
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                border=ft.border.all(1, "#F0F0F0"),
                content=ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.GAVEL, color=role_col, size=30), 
                        ft.Column([
                            ft.Text(aj.judge.name, weight="bold", size=16),
                            ft.Chip(label=ft.Text("Chairman" if aj.is_chairman else "Judge", size=10), bgcolor=ft.Colors.with_opacity(0.1, role_col))
                        ], spacing=2)
                    ]),
                    remove_icon
                ], alignment="spaceBetween")
            ))
            
        judges_tab_content.controls.append(ft.Column(cards, spacing=10))
        page.update()

    # ---------------------------------------------------------
    # EXPORT DIALOG LOGIC
    # ---------------------------------------------------------
    
    # 1. FILE PICKER CALLBACK
    def on_export_result(e: ft.FilePickerResultEvent):
        # We need to know which format was requested (stored in pending_export_type)
        if e.path:
            save_path = e.path
            
            # Fetch data needed for export
            db = SessionLocal()
            ev = db.query(Event).get(event_id)
            event_name = ev.name if ev else "Event"
            db.close()
            
            # DETERMINE DATA & MODE
            if selected_export_scope == "overall":
                data = pageant_service.get_overall_breakdown(event_id)
                mode = "overall"
                doc_title = "OFFICIAL OVERALL STANDINGS"
            else:
                # It's a segment ID
                try:
                    seg_id = int(selected_export_scope)
                    data = pageant_service.get_segment_tabulation(event_id, seg_id)
                    mode = "segment"
                    
                    # Fetch Segment Name for Title
                    db = SessionLocal()
                    seg = db.query(Segment).get(seg_id)
                    seg_name = seg.name.upper() if seg else "SEGMENT"
                    db.close()
                    
                    doc_title = f"OFFICIAL RESULTS: {seg_name}"
                except ValueError:
                    page.open(ft.SnackBar(ft.Text("Invalid selection"), bgcolor="red"))
                    return

            success = False
            
            try:
                if pending_export_type == "xlsx":
                    success = export_service.generate_excel(
                        filepath=save_path,
                        event_name=event_name,
                        title=doc_title,
                        data_matrix=data,
                        mode=mode
                    )
                elif pending_export_type == "pdf":
                    success = export_service.generate_pdf(
                        filepath=save_path,
                        event_name=event_name,
                        title=doc_title,
                        data_matrix=data,
                        mode=mode
                    )
                
                if success:
                    page.open(ft.SnackBar(ft.Text(f"Saved to: {save_path}"), bgcolor="green"))
                    # Try to open the file (Desktop only feature, but harmless on mobile)
                    try: os.startfile(save_path)
                    except: pass
                else:
                    page.open(ft.SnackBar(ft.Text("Export failed."), bgcolor="red"))
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red"))

    # 2. INIT PICKER
    export_picker = ft.FilePicker(on_result=on_export_result)
    page.overlay.append(export_picker)

    def run_export_trigger(file_type):
        nonlocal pending_export_type
        pending_export_type = file_type
        page.close(export_dialog)
        
        # Prepare filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        db = SessionLocal()
        ev = db.query(Event).get(event_id)
        event_name = ev.name if ev else "Event"
        db.close()
        
        # Clean filename of bad chars
        safe_name = "".join([c for c in event_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}_Results_{timestamp}.{file_type}"
        
        # Trigger "Save As" Dialog
        export_picker.save_file(
            dialog_title="Save Results As...",
            file_name=filename,
            allowed_extensions=[file_type]
        )

    # EXPORT SCOPE DROPDOWN
    export_scope_dd = ft.Dropdown(
        label="Data to Export",
        width=300,
        options=[], # Populated on open
        dense=True,
        bgcolor="white",
        border_color="#64AEFF",
    )
    
    def on_scope_change(e):
        nonlocal selected_export_scope
        selected_export_scope = export_scope_dd.value
        
    export_scope_dd.on_change = on_scope_change

    def open_export_dialog(e):
        # Refresh segments list
        db = SessionLocal()
        segments = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
        db.close()
        
        opts = [ft.dropdown.Option("overall", "Overall Summary (Segments as Columns)")]
        for s in segments:
            opts.append(ft.dropdown.Option(str(s.id), f"{s.name} (Judges as Columns)"))
            
        export_scope_dd.options = opts
        export_scope_dd.value = "overall"
        # Update state variable too
        nonlocal selected_export_scope
        selected_export_scope = "overall"
        
        # export_scope_dd.update() # Removed to prevent crash
        page.open(export_dialog)

    # The Dialog UI
    export_dialog = ft.AlertDialog(
        title=ft.Text("Export Results"),
        content=ft.Column([
            ft.Text("Select what to export:"),
            export_scope_dd,
            ft.Divider(),
            ft.Text("Select format:"),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TABLE_CHART, size=40, color="green"),
                        ft.Text("Excel (.xlsx)", weight="bold")
                    ], alignment="center", horizontal_alignment="center"),
                    padding=20,
                    bgcolor=ft.Colors.GREEN_50,
                    border_radius=10,
                    ink=True,
                    on_click=lambda e: run_export_trigger("xlsx"),
                    width=130, height=120,
                    border=ft.border.all(1, "green")
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=40, color="red"),
                        ft.Text("PDF Document", weight="bold")
                    ], alignment="center", horizontal_alignment="center"),
                    padding=20,
                    bgcolor=ft.Colors.RED_50,
                    border_radius=10,
                    ink=True,
                    on_click=lambda e: run_export_trigger("pdf"),
                    width=130, height=120,
                    border=ft.border.all(1, "red")
                )
            ], alignment="center", spacing=20)
        ], tight=True, width=400),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(export_dialog))
        ]
    )

    # =================================================================================================
    # TAB 4: TABULATION
    # =================================================================================================
    def refresh_scores_tab():
        scores_tab_content.controls.clear()
        
        # Header with Export
        scores_tab_content.controls.append(ft.Row([
            ft.Text("Tabulation Board", size=20, weight="bold"),
            ft.Row([
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda e: refresh_scores_tab()),
                ft.ElevatedButton(
                    "Export Scores", 
                    icon=ft.Icons.DOWNLOAD, 
                    on_click=open_export_dialog,
                    bgcolor="#64AEFF", color="white")
                ])
        ], alignment="spaceBetween"))

        # Tabs for Segments
        db = SessionLocal()
        segments = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
        db.close()

        def build_matrix(seg_id):
            if seg_id is None: # Overall
                data = pageant_service.get_overall_breakdown(event_id)
                cols = ["Rank", "#", "Name"] + data['segments'] + ["Total"]
                rows = []
                for gender in ['Male', 'Female']:
                    # Category Header
                    rows.append(
                        ft.DataRow(
                            cells=[ft.DataCell(ft.Text(f"{gender.upper()} DIVISION", weight="bold", color="white"))] + [ft.DataCell(ft.Text(""))]*(len(cols)-1),
                            color="#80C1FF" # Sub-header color
                        )
                    )
                    for i, r in enumerate(data[gender]):
                        row_color = "#F0F8FF" if i % 2 == 0 else "white"
                        cells = [
                            ft.DataCell(ft.Text(str(r['rank']), weight="bold")), 
                            ft.DataCell(ft.Container(content=ft.Text(str(r['number']), color="white", size=10, weight="bold"), bgcolor="black", padding=5, border_radius=4)), 
                            ft.DataCell(ft.Text(r['name'], weight="w500"))
                        ]
                        for s in r['segment_scores']: cells.append(ft.DataCell(ft.Text(str(s))))
                        cells.append(ft.DataCell(ft.Text(str(r['total']), weight="bold", color="#64AEFF")))
                        rows.append(ft.DataRow(cells, color=row_color))
            else: # Segment
                data = pageant_service.get_segment_tabulation(event_id, seg_id)
                cols = ["Rank", "#", "Name"] + data['judges'] + ["Average"]
                rows = []
                for gender in ['Male', 'Female']:
                    rows.append(
                        ft.DataRow(
                            cells=[ft.DataCell(ft.Text(f"{gender.upper()} DIVISION", weight="bold", color="white"))] + [ft.DataCell(ft.Text(""))]*(len(cols)-1),
                            color="#80C1FF"
                        )
                    )
                    for i, r in enumerate(data[gender]):
                        row_color = "#F0F8FF" if i % 2 == 0 else "white"
                        cells = [
                            ft.DataCell(ft.Text(str(r['rank']), weight="bold")), 
                            ft.DataCell(ft.Container(content=ft.Text(str(r['number']), color="white", size=10, weight="bold"), bgcolor="black", padding=5, border_radius=4)), 
                            ft.DataCell(ft.Text(r['name'], weight="w500"))
                        ]
                        for s in r['scores']: cells.append(ft.DataCell(ft.Text(str(s))))
                        cells.append(ft.DataCell(ft.Text(str(r['total']), weight="bold", color="#64AEFF")))
                        rows.append(ft.DataRow(cells, color=row_color))
            
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.DataTable(
                            columns=[ft.DataColumn(ft.Text(c, size=12, weight="bold", color="white")) for c in cols], 
                            rows=rows, 
                            heading_row_color="#64AEFF", # Leaderboard Blue
                            heading_row_height=50,
                            data_row_min_height=45,
                            column_spacing=20,
                            border_radius=10,
                            vertical_lines=ft.border.BorderSide(1, "#F0F0F0"),
                            horizontal_lines=ft.border.BorderSide(1, "#F0F0F0"),
                        )
                    ], 
                    scroll=ft.ScrollMode.ADAPTIVE, 
                    alignment=ft.MainAxisAlignment.CENTER # Centers the table in the Row
                ),
                padding=0,
                bgcolor="white",
                border=ft.border.all(1, "#E0E0E0"),
                border_radius=10,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
            )

        tabs = [ft.Tab(text="OVERALL", content=ft.Column([build_matrix(None)], scroll="adaptive", horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))]
        for s in segments:
            tabs.append(ft.Tab(text=s.name.upper(), content=ft.Column([build_matrix(s.id)], scroll="adaptive", horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)))

        scores_tab_content.controls.append(ft.Tabs(tabs=tabs, expand=True))
        page.update()

    # --- MAIN ASSEMBLY ---
    # Trigger initial load for all tabs
    refresh_config_tab()
    refresh_contestant_tab()
    refresh_judges_tab()
    refresh_scores_tab()

    return ft.Column(
        controls=[
            header,
            ft.Container(
                content=ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(text="Configuration", icon=ft.Icons.SETTINGS, content=ft.Container(config_tab_content, padding=20)),
                        ft.Tab(text="Contestants", icon=ft.Icons.PEOPLE, content=ft.Container(contestant_tab_content, padding=20)),
                        ft.Tab(text="Judges", icon=ft.Icons.GAVEL, content=ft.Container(judges_tab_content, padding=20)),
                        ft.Tab(text="Tabulation", icon=ft.Icons.LEADERBOARD, content=ft.Container(scores_tab_content, padding=20)),
                    ],
                    expand=True,
                    indicator_color="#64AEFF",
                    label_color="#64AEFF",
                    unselected_label_color="grey"
                ),
                padding=0,
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#DDF4FF", "#FDE9FF"]
                )
            )
        ],
        spacing=0,
        expand=True
    )