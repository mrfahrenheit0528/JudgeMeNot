import bcrypt
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from models.all_models import User, Event, Segment, Criteria, Contestant, EventJudge

def seed_data():
    print("🌱 Seeding database with Advanced Quiz Setup...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # =====================================================
        # 1. CREATE USERS
        # =====================================================
        # Password for all: 'pass123'
        password = "pass123".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt).decode('utf-8')

        users_config = [
            {"username": "admin", "name": "Super Admin", "role": "Admin"},
            # Judges for Pageant
            {"username": "judge1", "name": "Judge Judy", "role": "Judge"},
            {"username": "judge2", "name": "Simon Cowell", "role": "Judge"},
            # Tabulators for Quiz Bee (6 Tabs for 6 Teams)
            {"username": "tab1", "name": "Tabulator Alpha", "role": "Tabulator"},
            {"username": "tab2", "name": "Tabulator Beta", "role": "Tabulator"},
            {"username": "tab3", "name": "Tabulator Gamma", "role": "Tabulator"},
            {"username": "tab4", "name": "Tabulator Delta", "role": "Tabulator"},
            {"username": "tab5", "name": "Tabulator Epsilon", "role": "Tabulator"},
            {"username": "tab6", "name": "Tabulator Zeta", "role": "Tabulator"},
        ]

        user_map = {} # Cache to store objects

        for u in users_config:
            existing = db.query(User).filter(User.username == u['username']).first()
            if not existing:
                new_user = User(
                    username=u['username'],
                    password_hash=hashed,
                    name=u['name'],
                    role=u['role'],
                    is_active=True,
                    is_pending=False
                )
                db.add(new_user)
                db.flush() # Get ID
                user_map[u['username']] = new_user
                print(f"   [+] Created User: {u['username']}")
            else:
                user_map[u['username']] = existing
                print(f"   [.] User exists: {u['username']}")

        # =====================================================
        # 2. CREATE PAGEANT (Simplified)
        # =====================================================
        # Just creating the event structure so Pageant features don't break
        p_name = "Mr. & Ms. Intramurals 2025"
        if not db.query(Event).filter(Event.name == p_name).first():
            p_event = Event(name=p_name, event_type="Pageant", status="Active")
            db.add(p_event); db.flush()
            
            # Segments
            s1 = Segment(event_id=p_event.id, name="Talent", percentage_weight=0.4, order_index=1, is_active=True)
            s2 = Segment(event_id=p_event.id, name="Formal Wear", percentage_weight=0.6, order_index=2)
            db.add_all([s1, s2]); db.flush()
            
            # Criteria
            db.add(Criteria(segment_id=s1.id, name="Execution", weight=0.5))
            db.add(Criteria(segment_id=s1.id, name="Entertainment", weight=0.5))
            
            # Candidate
            db.add(Contestant(event_id=p_event.id, candidate_number=1, name="Juan Cruz", gender="Male"))
            
            # Judge Assignment
            db.add(EventJudge(event_id=p_event.id, judge_id=user_map['judge1'].id, is_chairman=True))
            print("   [+] Created Pageant Event")

        # =====================================================
        # 3. CREATE QUIZ BEE (The Main Test)
        # =====================================================
        q_name = "Inter-School Science Olympiad"
        q_event = db.query(Event).filter(Event.name == q_name).first()

        if not q_event:
            q_event = Event(name=q_name, event_type="QuizBee", status="Active")
            db.add(q_event)
            db.flush()
            print(f"   [+] Created Quiz Bee: {q_name}")

            # --- ROUNDS SETUP ---
            # Scenario: 6 Teams.
            # Round 1 (Easy):    Top 5 qualify (1 eliminated).
            # Round 2 (Average): Top 4 qualify (1 eliminated).
            # Round 3 (Diff):    Top 3 qualify (1 eliminated).
            # Final Round:       Top 1 wins.
            
            rounds = [
                {
                    "name": "Easy Round", "order": 1, "pts": 1, "qs": 5, 
                    "active": True, "final": False, "limit": 5
                },
                {
                    "name": "Average Round", "order": 2, "pts": 3, "qs": 5, 
                    "active": False, "final": False, "limit": 4
                },
                {
                    "name": "Difficult Round", "order": 3, "pts": 5, "qs": 5, 
                    "active": False, "final": False, "limit": 3
                },
                {
                    "name": "Grand Final", "order": 4, "pts": 10, "qs": 5, 
                    "active": False, "final": True, "limit": 1 # The Champion
                }
            ]

            for r in rounds:
                seg = Segment(
                    event_id=q_event.id,
                    name=r['name'],
                    order_index=r['order'],
                    points_per_question=r['pts'],
                    total_questions=r['qs'],
                    is_active=r['active'],
                    is_final=r['final'],
                    qualifier_limit=r['limit']
                )
                db.add(seg)
            db.flush()

            # --- TEAMS & ASSIGNMENTS ---
            teams = [
                {"num": 1, "name": "Team Alpha (UP)", "tab": "tab1"},
                {"num": 2, "name": "Team Beta (ADMU)", "tab": "tab2"},
                {"num": 3, "name": "Team Gamma (DLSU)", "tab": "tab3"},
                {"num": 4, "name": "Team Delta (UST)", "tab": "tab4"},
                {"num": 5, "name": "Team Epsilon (MIT)", "tab": "tab5"},
                {"num": 6, "name": "Team Zeta (CSPC)", "tab": "tab6"},
            ]

            for t in teams:
                # Find tabulator ID
                tab_user = user_map.get(t['tab'])
                tab_id = tab_user.id if tab_user else None
                
                contestant = Contestant(
                    event_id=q_event.id,
                    candidate_number=t['num'],
                    name=t['name'],
                    gender="Mixed", # Quiz bee usually mixed
                    status="Active",
                    assigned_tabulator_id=tab_id
                )
                db.add(contestant)
            
            print("   [+] Added 6 Teams and Assignments")
        
        else:
            print(f"   [.] Quiz Bee '{q_name}' already exists.")

        db.commit()
        print("\n✅ Seed completed successfully!")
        print("   Admin: admin / pass123")
        print("   Tabulators: tab1 to tab6 (Password: pass123)")
        print("   Judges: judge1 (Password: pass123)")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()