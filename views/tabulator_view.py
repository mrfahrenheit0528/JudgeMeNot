import flet as ft
import threading
import time
from services.quiz_service import QuizService
from services.event_service import EventService
from services.contestant_service import ContestantService
from core.database import SessionLocal
from models.all_models import Contestant, Segment, Score, Event
from components.dialogs import show_about_dialog, show_contact_dialog

def TabulatorView(page: ft.Page, on_logout_callback):
    # Services
    quiz_service = QuizService()
    event_service = EventService()
    contestant_service = ContestantService()

    # State
    tabulator_id = page.session.get("user_id")
    tabulator_name = page.session.get("user_name")
    
    current_event = None
    active_round = None
    assigned_contestant = None
    
    # State tracking for Auto-Refresh
    last_round_id = None
    last_question_count = 0
    is_polling = True
    
    # Track available events to prevent UI flicker
    cached_available_event_ids = set()
    
    # Local cache to store selections before saving
    answers_cache = {} 
    
    # UI Containers
    main_container = ft.Container(expand=True, padding=20,
                                                  gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#DDF4FF", "#FDE9FF"]
                ))
    score_list = ft.Column(scroll="adaptive", expand=True, spacing=10)

    # ---------------------------------------------------------
    # 1. LOGIC: EVENT SWITCHING
    # ---------------------------------------------------------
    def switch_event_click(e):
        nonlocal current_event, active_round, assigned_contestant, last_round_id, cached_available_event_ids
        current_event = None
        active_round = None
        assigned_contestant = None
        last_round_id = None
        
        # FIX: Reset the cache so the menu knows it needs to re-render
        cached_available_event_ids = set() 
        
        # Clearing the container will trigger the "Select Event" view on next poll
        # We use a Column with center alignment to prevent the "tall loading" issue
        main_container.content = ft.Column(
            controls=[
                ft.ProgressRing(),
                ft.Text("Loading...", color="grey")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        page.update()

    # ---------------------------------------------------------
    # 2. HEADER
    # ---------------------------------------------------------
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, color="white"),
                ft.Column([
                    ft.Text(f"Tabulator: {tabulator_name}", color="white", weight="bold"),
                    ft.Text("Quiz Bee Panel", size=12, color="white70")
                ], spacing=2)
            ]),
            ft.Row([
                ft.TextButton("Switch Event", icon=ft.Icons.SWAP_HORIZ, style=ft.ButtonStyle(color=ft.Colors.WHITE), on_click=switch_event_click, visible=True), # Always visible if logged in
                ft.VerticalDivider(width=10, color="white24"),
                ft.TextButton("Leaderboard", icon=ft.Icons.EMOJI_EVENTS, style=ft.ButtonStyle(color=ft.Colors.WHITE), on_click=lambda e: page.go("/leaderboard")),
                ft.TextButton("About", style=ft.ButtonStyle(color=ft.Colors.WHITE), on_click=lambda e: show_about_dialog(page)),
                ft.TextButton("Contact", style=ft.ButtonStyle(color=ft.Colors.WHITE), on_click=lambda e: show_contact_dialog(page)),
                ft.VerticalDivider(width=10, color="white24"),
                ft.IconButton(icon=ft.Icons.LOGOUT, icon_color="white", tooltip="Log Out", on_click=lambda e: stop_and_logout(e))
            ])
        ], alignment="spaceBetween"),
        padding=15, 
        bgcolor=ft.Colors.BLUE_800
    )

    def stop_and_logout(e):
        nonlocal is_polling
        is_polling = False
        on_logout_callback(e)

    # ---------------------------------------------------------
    # 3. DATA LOADING & POLLING
    # ---------------------------------------------------------
    def load_dashboard():
        nonlocal current_event, active_round, assigned_contestant, last_round_id, last_question_count, cached_available_event_ids
        
        # --- MODE A: NO EVENT SELECTED (Show Menu) ---
        if not current_event:
            db = SessionLocal()
            try:
                # 1. Find all active Quiz Bee events
                active_events = db.query(Event).filter(Event.status == "Active", Event.event_type == "QuizBee").all()
                
                # 2. Filter: Only show events where this tabulator is assigned
                my_events = []
                for ev in active_events:
                    # Check if there is a contestant in this event assigned to this tabulator
                    assignment = db.query(Contestant).filter(
                        Contestant.event_id == ev.id,
                        Contestant.assigned_tabulator_id == tabulator_id
                    ).first()
                    
                    if assignment:
                        my_events.append(ev)
                
                # Check for changes to prevent flickering
                current_ids = {e.id for e in my_events}
                if current_ids != cached_available_event_ids:
                    cached_available_event_ids = current_ids
                    render_event_selector(my_events)
                
                # AUTO-SELECT OPTIMIZATION: If only 1 event, just pick it
                # Logic Update: Only auto-select if we haven't cached anything yet (first load).
                # If we have cached IDs (meaning we just came from switch_event_click reset), don't auto-jump immediately if we want to show menu.
                # Actually, to keep it simple: If there is only 1 event, user is "locked" to it unless they have >1.
                # But if they click "Switch" and there's only 1, it will just reload that 1. 
                # That is acceptable behavior for 1 event.
                if len(my_events) == 1 and not cached_available_event_ids: 
                     pass 

            except Exception as e:
                print(f"Error fetching events: {e}")
            finally:
                db.close()
            return

        # --- MODE B: EVENT SELECTED (Show Scoring) ---
        
        # 1. Check Active Round
        active_round = event_service.get_active_segment(current_event.id)
        if not active_round:
            show_wait_screen("Waiting for Admin to start a round...", force_refresh=False)
            last_round_id = None
            return

        # 2. Check Assignment/School for this specific Event
        if not assigned_contestant:
            db = SessionLocal()
            assigned_contestant = db.query(Contestant).filter(
                Contestant.event_id == current_event.id,
                Contestant.assigned_tabulator_id == tabulator_id
            ).first()
            db.close()
        
        if not assigned_contestant:
            show_error(f"You are not assigned to any school/participant in '{current_event.name}'.")
            return

        # 3. Check Participation in current round
        if active_round.participating_school_ids:
            allowed_ids = [int(x) for x in active_round.participating_school_ids.split(",") if x.strip()]
            if assigned_contestant.id not in allowed_ids:
                show_wait_screen(f"Your school ({assigned_contestant.name}) is not participating in: {active_round.name}", force_refresh=False)
                last_round_id = None # Reset state so we re-check later
                return

        # 4. Update UI if needed
        if active_round.id != last_round_id or active_round.total_questions != last_question_count:
            render_scoring_ui()
            last_round_id = active_round.id
            last_question_count = active_round.total_questions

    def poll_updates():
        while is_polling:
            if page:
                try:
                    load_dashboard()
                except Exception as e: 
                    print(f"Polling error: {e}")
            time.sleep(2)

    # ---------------------------------------------------------
    # 4. UI RENDERERS
    # ---------------------------------------------------------
    def render_event_selector(events):
        def select_event(e):
            nonlocal current_event
            current_event = e.control.data
            # Centered loading screen
            main_container.content = ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("Loading...", color="grey")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
            page.update()
            # The next poll tick will pick up 'current_event' and load the round

        if not events:
            main_container.content = ft.Column([
                ft.Icon(ft.Icons.EVENT_BUSY, size=60, color="grey"),
                ft.Text("No active Quiz Bee events found for you.", size=18, color="grey")
            ], alignment="center", horizontal_alignment="center")
        else:
            cards = []
            for ev in events:
                cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.LIGHTBULB, size=40, color="orange"),
                            ft.Text(ev.name, weight="bold", size=16, text_align="center"),
                            ft.ElevatedButton("Enter Event", data=ev, on_click=select_event)
                        ], alignment="center", horizontal_alignment="center"),
                        bgcolor="white",
                        padding=20,
                        border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_300),
                        width=200,
                        height=200,
                        alignment=ft.alignment.center
                    )
                )
            
            main_container.content = ft.Column([
                ft.Text("Select Active Event", size=24, weight="bold"),
                ft.Text("You are assigned as a Tabulator for these events:", color="grey"),
                ft.Divider(),
                ft.Row(cards, wrap=True, spacing=20, run_spacing=20, alignment="center")
            ], horizontal_alignment="center")
        
        page.update()

    def show_error(msg):
        main_container.content = ft.Column([
            ft.Icon(ft.Icons.WARNING_AMBER, size=60, color="orange"),
            ft.Text(msg, size=18, text_align="center"),
            ft.ElevatedButton("Retry / Back", on_click=switch_event_click)
        ], alignment="center", horizontal_alignment="center")
        page.update()

    def show_wait_screen(msg, force_refresh=True):
        # Don't overwrite if it's already a wait screen with same msg to avoid flicker
        # (Simplified check)
        
        content = ft.Column([
            ft.Icon(ft.Icons.HOURGLASS_EMPTY, size=60, color="blue"),
            ft.Text("Please Wait", size=24, weight="bold"),
            ft.Text(msg, size=16, text_align="center", color="grey")
        ], alignment="center", horizontal_alignment="center")
        
        if force_refresh:
             content.controls.append(ft.OutlinedButton("Check for Updates", icon=ft.Icons.REFRESH, on_click=lambda e: load_dashboard()))
        
        main_container.content = content
        page.update()

    def render_scoring_ui():
        score_list.controls.clear()
        answers_cache.clear()
        
        info_card = ft.Container(padding=15, bgcolor=ft.Colors.BLUE_50, border_radius=10, content=ft.Row([
                ft.Column([ft.Text("Event", size=12, color="grey"), ft.Text(current_event.name, weight="bold")]),
                ft.Column([ft.Text("Current Round", size=12, color="grey"), ft.Text(active_round.name, weight="bold", color="blue")]),
                ft.Column([ft.Text("Assigned To", size=12, color="grey"), ft.Text(assigned_contestant.name, weight="bold", size=18, color="black")])
            ], alignment="spaceBetween"))

        total_qs = active_round.total_questions
        limit = total_qs if total_qs > 0 else 20 

        db = SessionLocal()
        existing_scores = db.query(Score).filter(Score.contestant_id == assigned_contestant.id, Score.segment_id == active_round.id).all()
        db.close()
        
        score_map = {s.question_number: s.is_correct for s in existing_scores}

        for i in range(1, limit + 1):
            q_num = i
            current_val = score_map.get(q_num, None)
            if current_val is not None: answers_cache[q_num] = current_val

            rg = ft.RadioGroup(content=ft.Row([ft.Radio(value="correct", label="Correct", fill_color="green"), ft.Radio(value="wrong", label="Wrong", fill_color="red")]), value="correct" if current_val is True else "wrong" if current_val is False else None, on_change=lambda e, q=q_num: update_cache(q, e.control.value))
            row = ft.Container(padding=10, bgcolor="white", border_radius=8, border=ft.border.all(1, ft.Colors.GREY_200), content=ft.Row([ft.Text(f"Q{q_num}", weight="bold", size=16, width=50), rg], alignment="spaceBetween"))
            score_list.controls.append(row)

        submit_btn = ft.ElevatedButton("Save & Submit Answers", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN, color="white", height=50, width=250, on_click=save_all_scores)

        main_container.content = ft.Column([info_card, ft.Divider(), ft.Text("Mark Answers:", weight="bold"), ft.Container(score_list, expand=True), ft.Container(content=submit_btn, alignment=ft.alignment.center, padding=10)], expand=True)
        page.update()

    def update_cache(q_num, value):
        answers_cache[q_num] = (value == "correct")

    def save_all_scores(e):
        if not answers_cache: page.open(ft.SnackBar(ft.Text("No answers marked yet."), bgcolor="orange")); return
        e.control.text = "Saving..."; e.control.disabled = True; page.update()
        errors = 0
        for q_num, is_correct in answers_cache.items():
            success, msg = quiz_service.submit_answer(tabulator_id, assigned_contestant.id, active_round.id, q_num, is_correct)
            if not success: errors += 1
        if errors > 0: page.open(ft.SnackBar(ft.Text(f"Saved with {errors} errors."), bgcolor="red"))
        else: page.open(ft.SnackBar(ft.Text("All scores saved successfully!"), bgcolor="green"))
        e.control.text = "Save & Submit Answers"; e.control.disabled = False; page.update()

    # Initial Load & Start Polling
    threading.Thread(target=poll_updates, daemon=True).start()

    return ft.Column([header, main_container], expand=True)