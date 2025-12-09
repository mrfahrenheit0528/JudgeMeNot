import flet as ft
import threading
import time
from services.quiz_service import QuizService
from services.contestant_service import ContestantService
from services.admin_service import AdminService
from services.event_service import EventService
from core.database import SessionLocal
from models.all_models import Segment, Contestant, User, Score, Event
from sqlalchemy import func
from components.dialogs import show_about_dialog, show_contact_dialog
import itertools 

def QuizConfigView(page: ft.Page, event_id: int):
    # Services
    quiz_service = QuizService()
    contestant_service = ContestantService()
    admin_service = AdminService()
    event_service = EventService()

    # --- FETCH EVENT DETAILS FOR HEADER ---
    db = SessionLocal()
    event_obj = db.query(Event).get(event_id)
    event_name = event_obj.name if event_obj else "Quiz Bee Event"
    db.close()

    # State
    current_admin_id = page.session.get("user_id")
    user_role = page.session.get("user_role")
    is_read_only = (user_role == "AdminViewer")

    editing_round_id = None 
    editing_contestant_id = None 
    is_polling = False
    
    # Global component references
    eval_btn_ref = ft.Ref[ft.ElevatedButton]()

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

    # ---------------------------------------------------------
    # 1. CONFIGURATION TAB (Rounds)
    # ---------------------------------------------------------
    q_order = ft.TextField(label="Round #", width=100, keyboard_type=ft.KeyboardType.NUMBER, dense=True)
    q_round_name = ft.TextField(label="Round Name (e.g. Easy)", width=300, dense=True)
    q_points = ft.TextField(label="Pts/Question", width=140, keyboard_type=ft.KeyboardType.NUMBER, dense=True)
    q_total_qs = ft.TextField(label="Total Qs", width=140, keyboard_type=ft.KeyboardType.NUMBER, hint_text="0 for unlimited", dense=True)
    q_is_final = ft.Checkbox(label="Is Final Round/Back-to-Zero?", value=False)
    q_qualifiers = ft.TextField(label="Qualifiers (Top N)", width=200, keyboard_type=ft.KeyboardType.NUMBER, visible=True, dense=True)

    def on_final_check(e): pass
    q_is_final.on_change = on_final_check

    def save_round(e):
        try:
            order = int(q_order.value); pts = float(q_points.value) if q_points.value else 1.0
            qs = int(q_total_qs.value) if q_total_qs.value else 0; limit = int(q_qualifiers.value) if q_qualifiers.value else 0
            if editing_round_id: success, msg = quiz_service.update_round(current_admin_id, editing_round_id, q_round_name.value, pts, qs, order, q_is_final.value, limit)
            else: success, msg = quiz_service.add_round(current_admin_id, event_id, q_round_name.value, pts, qs, order, is_final=q_is_final.value, qualifier_limit=limit)
            if success:
                page.open(ft.SnackBar(ft.Text("Saved!"), bgcolor="green")); page.close(round_dialog)
                q_order.value = str(order + 1); q_round_name.value = ""; refresh_config_tab()
            else: page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
        except: page.open(ft.SnackBar(ft.Text("Invalid Input"), bgcolor="red"))

    def delete_round(round_id):
        def confirm_delete(e):
            page.close(del_dlg)
            success, msg = quiz_service.delete_round(current_admin_id, round_id)
            if success:
                page.open(ft.SnackBar(ft.Text("Round Deleted"), bgcolor="orange"))
                refresh_config_tab()
            else:
                page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))

        del_dlg = ft.AlertDialog(
            title=ft.Text("Delete Round?"),
            content=ft.Text("This will also delete ALL scores associated with this round. Are you sure?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(del_dlg)),
                ft.ElevatedButton("Delete", bgcolor="red", color="white", on_click=confirm_delete)
            ]
        )
        page.open(del_dlg)

    round_dialog = ft.AlertDialog(
        title=ft.Text("Config Quiz Round"),
        content=ft.Column([ft.Row([q_order, q_round_name]), ft.Row([q_points, q_total_qs]), ft.Divider(), ft.Text("Rules"), ft.Row([q_qualifiers, q_is_final])], height=250, width=450, tight=True),
        actions=[ft.TextButton("Save", on_click=save_round)]
    )

    def open_add_round_dialog(e): nonlocal editing_round_id; editing_round_id = None; q_order.value = ""; q_round_name.value = ""; q_points.value = ""; q_total_qs.value = ""; q_qualifiers.value = ""; q_is_final.value = False; round_dialog.title.value = "Add Quiz Round"; page.open(round_dialog)
    def open_edit_round_dialog(e): nonlocal editing_round_id; d = e.control.data; editing_round_id = d.id; q_order.value = str(d.order_index); q_round_name.value = d.name; q_points.value = str(int(d.points_per_question)); q_total_qs.value = str(d.total_questions); q_qualifiers.value = str(d.qualifier_limit); q_is_final.value = d.is_final; round_dialog.title.value = "Edit Quiz Round"; page.open(round_dialog)

    config_container = ft.Column(spacing=15, scroll="adaptive", expand=True)
    
    def refresh_config_tab():
        config_container.controls.clear()
        
        # Hide Add Button if Read Only
        add_round_btn = ft.ElevatedButton("Add Round", icon=ft.Icons.ADD, on_click=open_add_round_dialog, bgcolor="#64AEFF", color="white") if not is_read_only else ft.Container()
        
        # Header
        config_container.controls.append(ft.Row([
            ft.Text("Quiz Rounds Sequence", size=24, weight="bold"),
            add_round_btn
        ], alignment="spaceBetween"))
        
        db = SessionLocal(); rounds = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all(); db.close()
        
        for r in rounds:
            # Modern Round Card
            is_final_style = ft.Colors.AMBER_100 if r.is_final else "white"
            round_badge = "Final" if r.is_final else "Prelim"
            
            # Action Buttons
            if not is_read_only:
                actions = ft.Row([
                    ft.Chip(label=ft.Text(f"Qualifiers: {r.qualifier_limit}"), bgcolor=ft.Colors.BLUE_50),
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color="blue", tooltip="Edit", data=r, on_click=open_edit_round_dialog),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", tooltip="Delete", data=r.id, on_click=lambda e: delete_round(e.control.data))
                ])
            else:
                actions = ft.Chip(label=ft.Text(f"Qualifiers: {r.qualifier_limit}"), bgcolor=ft.Colors.BLUE_50)

            card = ft.Container(
                padding=20,
                bgcolor="white",
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                border=ft.border.all(1, "#E0E0E0"),
                content=ft.Row([
                    ft.Row([
                        ft.Container(content=ft.Text(f"#{r.order_index}", color="white", weight="bold"), bgcolor="black", padding=10, border_radius=50, width=40, height=40, alignment=ft.alignment.center),
                        ft.Column([
                            ft.Text(r.name, weight="bold", size=16),
                            ft.Row([
                                ft.Icon(ft.Icons.HELP_OUTLINE, size=14, color="grey"),
                                ft.Text(f"{r.total_questions} Questions", size=12, color="grey"),
                                ft.Container(width=10),
                                ft.Icon(ft.Icons.STAR_BORDER, size=14, color="grey"),
                                ft.Text(f"{int(r.points_per_question)} Pts/Q", size=12, color="grey"),
                            ])
                        ], spacing=2)
                    ]),
                    actions
                ], alignment="spaceBetween")
            )
            config_container.controls.append(card)
        page.update()

    # ---------------------------------------------------------
    # 2. CONTESTANTS TAB
    # ---------------------------------------------------------
    c_number = ft.TextField(label="#", width=80, dense=True)
    c_name = ft.TextField(label="Name", width=250, dense=True)
    c_tab = ft.Dropdown(label="Tabulator", width=250, dense=True)
    
    contestant_container = ft.Column(spacing=15, scroll="adaptive", expand=True)
    
    def load_tabs(cur_tab_id=None): 
        db=SessionLocal()
        all_tabs = db.query(User).filter(User.role=="Tabulator").all()
        used = db.query(Contestant).filter(Contestant.event_id == event_id).all()
        used_ids = [c.assigned_tabulator_id for c in used if c.assigned_tabulator_id is not None]
        db.close()
        options = []
        for t in all_tabs:
            if t.id not in used_ids or (cur_tab_id and t.id == int(cur_tab_id)):
                options.append(ft.dropdown.Option(str(t.id), t.name))
        c_tab.options = options
        if c_tab.page:
            c_tab.update()

    def save_c(e): 
        try: 
            tab_id = int(c_tab.value) if c_tab.value else None
            if editing_contestant_id: success, msg = contestant_service.update_contestant(editing_contestant_id, int(c_number.value), c_name.value, "Mixed", assigned_tabulator_id=tab_id)
            else: success, msg = contestant_service.add_contestant(event_id, int(c_number.value), c_name.value, "Mixed", assigned_tabulator_id=tab_id)
            if success: page.close(c_dialog); refresh_c_tab()
            else: page.open(ft.SnackBar(ft.Text(msg), bgcolor="red"))
        except ValueError: page.open(ft.SnackBar(ft.Text("Invalid Input"), bgcolor="red"))

    c_dialog = ft.AlertDialog(title=ft.Text("Contestant"), content=ft.Column([c_number, c_name, c_tab], height=200), actions=[ft.TextButton("Save", on_click=save_c)])
    def open_add_c_dialog(e): nonlocal editing_contestant_id; editing_contestant_id = None; c_number.value = ""; c_name.value = ""; c_tab.value = None; load_tabs(None); page.open(c_dialog)
    def open_edit_c_dialog(e): nonlocal editing_contestant_id; d = e.control.data; editing_contestant_id = d.id; c_number.value = str(d.candidate_number); c_name.value = d.name; c_tab.value = str(d.assigned_tabulator_id) if d.assigned_tabulator_id else None; load_tabs(d.assigned_tabulator_id); page.open(c_dialog)

    def delete_contestant(cid): contestant_service.delete_contestant(cid); refresh_contestant_tab()
    def refresh_c_tab(): refresh_contestant_tab() # Alias
    def refresh_contestant_tab():
        contestant_container.controls.clear()
        
        # Header
        add_btn = ft.ElevatedButton("Add", icon=ft.Icons.ADD, on_click=open_add_c_dialog, bgcolor="#64AEFF", color="white") if not is_read_only else ft.Container()
        
        contestant_container.controls.append(ft.Row([
            ft.Text("Participating Schools", size=24, weight="bold"),
            add_btn
        ], alignment="spaceBetween"))
        
        db=SessionLocal()
        cs = db.query(Contestant).filter(Contestant.event_id==event_id).all()
        tab_ids = [c.assigned_tabulator_id for c in cs if c.assigned_tabulator_id]; tab_map = {}
        if tab_ids: tabs = db.query(User).filter(User.id.in_(tab_ids)).all(); tab_map = {t.id: t.name for t in tabs}
        db.close()
        
        for c in cs:
            tab_name = tab_map.get(c.assigned_tabulator_id, "Unassigned")
            tab_color = "green" if c.assigned_tabulator_id else "orange"
            
            # Actions
            if not is_read_only:
                actions = ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color="blue", data=c, on_click=open_edit_c_dialog),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", data=c.id, on_click=lambda e: delete_contestant(e.control.data))
                ])
            else:
                actions = ft.Container()

            contestant_container.controls.append(
                ft.Container(
                    padding=15, 
                    bgcolor="white", 
                    border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                    border=ft.border.all(1, "#F0F0F0"),
                    content=ft.Row([
                        ft.Row([
                            ft.Container(content=ft.Text(f"#{c.candidate_number}", color="white", weight="bold"), bgcolor="#64AEFF", padding=10, border_radius=8),
                            ft.Column([
                                ft.Text(c.name, weight="bold", size=16),
                                ft.Row([
                                    ft.Icon(ft.Icons.ASSIGNMENT_IND, size=14, color=tab_color),
                                    ft.Text(f"Tabulator: {tab_name}", size=12, color=tab_color)
                                ])
                            ], spacing=2)
                        ]),
                        actions
                    ], alignment="spaceBetween")
                )
            )
        page.update()

    # ---------------------------------------------------------
    # 3. MISSION CONTROL (Tabulation)
    # ---------------------------------------------------------
    tabulation_container = ft.Container(expand=True)

    def refresh_tabulation_tab():
        db = SessionLocal()
        active_seg = event_service.get_active_segment(event_id)
        
        # --- LEFT PANEL (Rounds) ---
        left_controls = []
        rounds = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
        for r in rounds:
            is_active = (active_seg and active_seg.id == r.id)
            
            # Styles
            bg_color = ft.Colors.BLUE_600 if is_active else "white"
            text_color = "white" if is_active else "black"
            sub_text_color = "white70" if is_active else "grey"
            border_side = ft.border.all(1, "transparent") if is_active else ft.border.all(1, "#E0E0E0")
            
            btn_text = "STOP" if is_active else "START"
            btn_bg = "white" if is_active else ft.Colors.GREEN_50
            btn_fg = "red" if is_active else "green"
            
            # Action Controls (Only for Admin)
            if not is_read_only:
                if "Clincher" in r.name and is_active:
                    action_area = ft.Row([
                        ft.ElevatedButton("+1 Q", bgcolor="orange", color="white", width=60, style=ft.ButtonStyle(padding=5), data=r.id, on_click=lambda e: add_clincher_question(e.control.data)),
                        ft.IconButton(icon=ft.Icons.STOP_CIRCLE, icon_color="white", data=r.id, on_click=lambda e: toggle_round_from_control(e.control.data))
                    ], spacing=2)
                else:
                    action_area = ft.ElevatedButton(btn_text, bgcolor=btn_bg, color=btn_fg, width=80, data=r.id, on_click=lambda e: toggle_round_from_control(e.control.data))
            else:
                # For AdminViewer, show status text instead of buttons
                status_label = "RUNNING" if is_active else "IDLE"
                action_area = ft.Container(content=ft.Text(status_label, color=text_color, size=12, weight="bold"), padding=5)

            left_controls.append(
                ft.Container(
                    bgcolor=bg_color, 
                    border_radius=10, 
                    padding=15, 
                    border=border_side,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12) if not is_active else None,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(r.name, color=text_color, weight="bold", size=14),
                            ft.Text(f"{r.total_questions} Qs • {int(r.points_per_question)} pts", color=sub_text_color, size=11)
                        ], spacing=2, expand=True), 
                        action_area
                    ], alignment="spaceBetween"),
                    margin=ft.margin.only(bottom=10)
                )
            )
        
        # --- RIGHT PANEL (Live Stats) ---
        results = []
        is_clincher = (active_seg and "Clincher" in active_seg.name)
        
        participants_data = quiz_service.get_participants_for_active_round(event_id, active_seg)
        participants = participants_data['participants']
        total_qs_in_round = active_seg.total_questions if active_seg else 0
        
        if active_seg:
            should_reset = is_clincher or active_seg.is_final or "Final" in active_seg.name
            if should_reset:
                results = quiz_service.get_live_scores(event_id, specific_round_id=active_seg.id)
            else:
                results = quiz_service.get_live_scores(event_id)
        else:
            results = quiz_service.get_live_scores(event_id)

        if participants_data['is_filtered']:
            p_ids = [p['id'] for p in participants]
            results = [r for r in results if r['contestant_id'] in p_ids]

        # Scoring Completion Logic
        is_ready_to_advance = False
        completion_status = quiz_service.check_scoring_completion(event_id, active_seg, participants, total_qs_in_round)
        unsubmitted_count = len(completion_status['unsubmitted'])
        
        if active_seg and active_seg.qualifier_limit > 0 and unsubmitted_count == 0 and total_qs_in_round > 0:
            is_ready_to_advance = True
            
        warning_msg = ft.Container(visible=False)
        if active_seg and not is_ready_to_advance and total_qs_in_round > 0:
            warning_msg = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color="white"),
                    ft.Text(f"{unsubmitted_count} team(s) incomplete. Cannot evaluate.", size=14, color="white", weight="bold")
                ], alignment="center"),
                bgcolor=ft.Colors.RED_400, padding=10, border_radius=5, visible=True
            )
            
        # --- TABLE CONSTRUCTION ---
        rows = []
        limit = active_seg.qualifier_limit if active_seg else 0
        max_possible_score = total_qs_in_round * active_seg.points_per_question if active_seg else 100
        
        for i, res in enumerate(results):
            rank = i+1
            color = ft.Colors.GREEN_50 if limit > 0 and rank <= limit else "white"
            
            # --- PROGRESS BAR (NEW) ---
            current_score = res['total_score']
            
            # Calculate actual completion ratio from participant data
            p_info = next((p for p in participants if p['id'] == res['contestant_id']), None)
            
            if p_info and total_qs_in_round > 0:
                completion_ratio = min(p_info.get('progress_count', 0) / total_qs_in_round, 1.0)
            elif total_qs_in_round == 0:
                 completion_ratio = 1.0
            else:
                 completion_ratio = 0.0

            # Find submission status icon
            is_done = p_info.get('is_complete') if p_info else False
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=18) if is_done else ft.Icon(ft.Icons.PENDING, color="orange", size=18)
            
            # UPDATED PROGRESS BAR: Thicker and with label beside it
            progress_row = ft.Row([
                ft.ProgressBar(value=completion_ratio, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.GREY_200, width=120, bar_height=10, border_radius=5),
                ft.Text(f"{int(completion_ratio*100)}%", size=12, weight="bold", color="grey")
            ], alignment="start", vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

            rows.append(ft.DataRow(
                color=color, 
                cells=[
                    ft.DataCell(ft.Text(str(rank), weight="bold")), 
                    ft.DataCell(ft.Row([ft.Text(res['name'], weight="w500"), status_icon], spacing=10)), 
                    ft.DataCell(ft.Text(str(current_score), weight="bold", color="blue")),
                    ft.DataCell(progress_row)
                ]
            ))

        table_card = ft.Container(
            content=ft.Column([
                 ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Rank", color="white", weight="bold")), 
                        ft.DataColumn(ft.Text("Name", color="white", weight="bold")), 
                        ft.DataColumn(ft.Text("Score", color="white", weight="bold")),
                        ft.DataColumn(ft.Text("Progress", color="white", weight="bold")), 
                    ], 
                    rows=rows,
                    heading_row_color="#64AEFF",
                    heading_row_height=50,
                    data_row_min_height=50,
                    column_spacing=30,
                    border_radius=10,
                    width=float("inf")
                )
            ], scroll="adaptive", expand=True),
            bgcolor="white",
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
            border=ft.border.all(1, "#E0E0E0"),
            expand=True,
            padding=0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )
        
        # Hide Evaluate Button for Auditor
        eval_btn = ft.ElevatedButton(
            "Evaluate & Advance", 
            ref=eval_btn_ref, 
            bgcolor=ft.Colors.GREEN, 
            color="white", 
            width=float("inf"), 
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: evaluate_round(is_ready_to_advance),
            disabled=not is_ready_to_advance,
            visible=not is_read_only # HIDE IF READ ONLY
        )
        
        # Assemble Right Panel
        right_panel_content = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Live Standings", size=20, weight="bold"),
                    ft.Text(f"Round: {active_seg.name if active_seg else 'None'}", color="grey", size=12)
                ], spacing=2), 
                # REMOVED CHIP HERE
            ], alignment="spaceBetween"),
            warning_msg, 
            table_card, 
            ft.Container(eval_btn, padding=ft.padding.only(top=10))
        ], expand=True)

        tabulation_container.content = ft.Row([
            ft.Container(content=ft.Column([
                ft.Text("Rounds Panel", weight="bold", size=16, color="grey"), 
                ft.Column(left_controls, scroll="auto", expand=True)
            ], expand=True), width=300, padding=10), 
            ft.VerticalDivider(width=1, color="#E0E0E0"), 
            ft.Container(content=right_panel_content, expand=True, padding=20)
        ], expand=True)
        
        db.close(); page.update()

    # ... (Rest of logic remains the same)
    
    def toggle_round_from_control(seg_id):
        active_seg = event_service.get_active_segment(event_id)
        if active_seg and active_seg.id == seg_id: event_service.set_active_segment(event_id, None)
        else: event_service.set_active_segment(event_id, seg_id)
        refresh_tabulation_tab()

    def add_clincher_question(seg_id):
        db = SessionLocal(); seg = db.query(Segment).get(seg_id)
        if seg: seg.total_questions += 1; db.commit(); page.open(ft.SnackBar(ft.Text("Question Added!"), bgcolor="green")); refresh_tabulation_tab()
        db.close()

    def evaluate_round(is_ready):
        if not is_ready:
             page.open(ft.SnackBar(ft.Text("All teams must submit scores before evaluation."), bgcolor="red"))
             return
             
        active_seg = event_service.get_active_segment(event_id)
        if not active_seg: return
        limit = active_seg.qualifier_limit
        if limit <= 0: page.open(ft.SnackBar(ft.Text("No limit set (Unlimited qualifiers)."), bgcolor="grey")); return

        db = SessionLocal()
        current_node = db.query(Segment).get(active_seg.id)
        root_node = current_node
        while root_node.related_segment_id:
            root_node = db.query(Segment).get(root_node.related_segment_id)
        is_final_chain = root_node.is_final
        db.close()

        is_clincher = "Clincher" in active_seg.name
        should_reset = is_clincher or is_final_chain
        
        results = quiz_service.get_live_scores(event_id, specific_round_id=active_seg.id if should_reset else None)
        
        if should_reset and active_seg.participating_school_ids:
             db = SessionLocal()
             p_ids = [int(x) for x in active_seg.participating_school_ids.split(",") if x.strip()]
             results = [r for r in results if r['contestant_id'] in p_ids]
             db.close()

        if len(results) <= limit and not is_final_chain: 
            page.open(ft.SnackBar(ft.Text("All participants qualify automatically."), bgcolor="green")); return

        if not is_final_chain:
            if len(results) < limit: 
                show_advance_dialog(results, active_seg.id, is_event_end=False)
                return
            last_in_score = results[limit-1]['total_score']
            first_out_score = results[limit]['total_score']
            
            if last_in_score == first_out_score:
                tied = [r for r in results if r['total_score'] == last_in_score]
                clean_winners = [r for r in results if r['total_score'] > last_in_score]
                spots_remaining = limit - len(clean_winners)

                def execute_tie_break(e):
                    page.close(dlg)
                    clean_ids = [r['contestant_id'] for r in clean_winners]
                    if clean_ids:
                        perform_advance(active_seg.id, clean_ids)
                    trigger_clincher_round(active_seg, tied, "Cutoff", spots_remaining)
                
                dlg = ft.AlertDialog(title=ft.Text("Tie at Cutoff!"), content=ft.Column([ft.Text(f"We need Top {limit}, but there is a tie for the last spots."), ft.Text(f"Qualified (Clean): {len(clean_winners)}"), ft.Text(f"Fighting for: {spots_remaining} spot(s)"), ft.Text(f"Candidates Tied: {len(tied)}")], tight=True), actions=[ft.ElevatedButton("Create Cutoff Clincher", bgcolor="orange", color="white", on_click=execute_tie_break)])
                page.open(dlg)
            else:
                show_advance_dialog(results[:limit], active_seg.id, is_event_end=False)
            return

        ties_found = [] 
        grouped_results = []
        for key, group in itertools.groupby(results, lambda x: x['total_score']):
            grouped_results.append((key, list(group)))
        
        current_rank = 1
        for score, participants in grouped_results:
            count = len(participants)
            if current_rank <= limit:
                if count > 1:
                    is_deadlock = False
                    if is_clincher and len(results) == count:
                        is_deadlock = True
                    names = [p['name'] for p in participants]
                    tie_data = {"rank": current_rank, "score": score, "participants": participants, "names": ", ".join(names), "is_deadlock": is_deadlock}
                    ties_found.append(tie_data)
            current_rank += count

        if ties_found:
            tie_controls = []
            for t in ties_found:
                if t['is_deadlock']:
                    action_btn = ft.ElevatedButton("Deadlock! Add +1 Question", bgcolor="red", color="white", height=30, on_click=lambda e: (page.close(dlg), add_clincher_question(active_seg.id)))
                    status_text = ft.Text(f"DEADLOCK: All {len(t['participants'])} participants tied.", color="red", weight="bold")
                else:
                    action_btn = ft.ElevatedButton(f"Resolve Rank {t['rank']} (New Round)", bgcolor="orange", color="white", height=30, data=t, on_click=lambda e, data=t: (page.close(dlg), trigger_clincher_round(active_seg, data['participants'], f"Rank {data['rank']}", 1)))
                    status_text = ft.Text(f"Partial Tie for Rank {t['rank']} ({t['score']} pts)", weight="bold", color="orange")
                tie_controls.append(ft.Container(padding=10, bgcolor=ft.Colors.ORANGE_50, border=ft.border.all(1, "orange"), border_radius=5, content=ft.Column([status_text, ft.Text(f"{t['names']}", size=12), action_btn])))

            dlg = ft.AlertDialog(title=ft.Row([ft.Icon(ft.Icons.WARNING, color="red"), ft.Text("Ties Detected!")]), content=ft.Column([ft.Text(f"Sudden Death / Tie Breaker Required."), ft.Divider(), ft.Column(tie_controls, spacing=10, scroll="auto", height=200)], tight=True, width=500), actions=[ft.TextButton("Cancel", on_click=lambda e: page.close(dlg))])
            page.open(dlg)
        else:
            show_advance_dialog(results[:limit], active_seg.id, is_event_end=is_final_chain)

    def end_event():
        event_service.set_active_segment(event_id, None)
        page.open(ft.SnackBar(ft.Text("Congratulations! Event Concluded."), bgcolor="green"))
        refresh_tabulation_tab()
        time.sleep(1)
        page.go(f"/leaderboard/{event_id}")

    def show_advance_dialog(qualifiers, seg_id, is_event_end=False):
        
        def on_confirm(e):
            page.close(adv_dlg)
            if is_event_end:
                end_event()
            else:
                perform_advance(seg_id, [q['contestant_id'] for q in qualifiers])

        btn_text = "End Event & Leaderboard" if is_event_end else "Advance/Finalize"
        btn_col = "purple" if is_event_end else "green"

        adv_dlg = ft.AlertDialog(title=ft.Text("Official Results"), content=ft.Column([ft.Text(f"Results confirmed. No ties detected. {'(Event Finished)' if is_event_end else ''}"), ft.Column([ft.Text(f"{i+1}. {q['name']} ({q['total_score']} pts)") for i, q in enumerate(qualifiers)], height=150, scroll="auto")], tight=True), actions=[ft.ElevatedButton(btn_text, bgcolor=btn_col, color="white", on_click=on_confirm)])
        page.open(adv_dlg)

    def trigger_clincher_round(active_round, tied_participants, label_suffix, spots_needed):
        db = SessionLocal()
        last_round = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index.desc()).first()
        new_order = (last_round.order_index + 1) if last_round else 1
        
        tied_ids = [p['contestant_id'] for p in tied_participants]
        parent_id = active_round.id
        new_name = f"Clincher for {label_suffix}"
        if "Clincher" in active_round.name: new_name = f"Sub-{new_name}"

        success, clincher_id = quiz_service.add_round(current_admin_id, event_id, new_name, points=1, total_questions=1, order=new_order, is_final=False, qualifier_limit=spots_needed, participating_ids=tied_ids, related_id=parent_id)
        
        if success:
            for p_id in tied_ids:
                db.add(Score(contestant_id=p_id, segment_id=clincher_id, judge_id=current_admin_id, question_number=1, score_value=0, is_correct=False)) 
            db.commit()
            
            event_service.set_active_segment(event_id, clincher_id)
            page.open(ft.SnackBar(ft.Text(f"Clincher Created: {new_name}"), bgcolor="orange"))
            refresh_tabulation_tab()
        
        db.close()

    def perform_advance(current_round_id, qual_ids):
        success, msg = quiz_service.advance_to_next_round(current_admin_id, event_id, current_round_id, qual_ids)
        if success: page.open(ft.SnackBar(ft.Text(msg), bgcolor="green")); refresh_tabulation_tab()
        else: page.open(ft.SnackBar(ft.Text(msg), bgcolor="red"))

    # --- AUTO REFRESH ---
    def poll_updates():
        while is_polling:
            if page: 
                try: refresh_tabulation_tab()
                except: break
            time.sleep(3)

    main_tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="Config", icon=ft.Icons.SETTINGS, content=ft.Container(config_container, padding=20)),
            ft.Tab(text="Contestants", icon=ft.Icons.PEOPLE, content=ft.Container(contestant_container, padding=20)),
            ft.Tab(text="Mission Control", icon=ft.Icons.ROCKET_LAUNCH, content=ft.Container(tabulation_container, padding=0))
        ],
        on_change=lambda e: load_tab(e.control.selected_index),
        expand=True,
        indicator_color="#64AEFF",
        label_color="#64AEFF",
        unselected_label_color="grey"
    )
    def load_tab(idx):
        nonlocal is_polling
        is_polling = (idx == 2)
        if is_polling: 
            if not any(t.daemon and t.is_alive() for t in threading.enumerate() if t.name == "QuizPoll"):
                 threading.Thread(target=poll_updates, daemon=True, name="QuizPoll").start()
            refresh_tabulation_tab()
        elif idx==0: refresh_config_tab()
        elif idx==1: refresh_c_tab()

    refresh_config_tab()
    return ft.Column(
        controls=[
            header,
            ft.Container(content=main_tabs, padding=10, expand=True, bgcolor="#F5F7FA")
        ],
        spacing=0,
        expand=True
    )