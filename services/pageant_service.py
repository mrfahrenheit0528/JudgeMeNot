from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import SessionLocal
from models.all_models import Segment, Criteria, Score, Contestant, Event

class PageantService:
    # ---------------------------------------------------------
    # SEGMENT MANAGEMENT
    # ---------------------------------------------------------
    def add_segment(self, event_id, name, weight, order):
        db = SessionLocal()
        try:
            # VALIDATION: Check total weight of segments
            current_total = db.query(func.sum(Segment.percentage_weight))\
                .filter(Segment.event_id == event_id).scalar() or 0.0
            
            # Allow a tiny float margin (1.0001)
            if (current_total + weight) > 1.0001:
                return False, f"Total exceeds 100%. Current: {int(current_total*100)}%, Adding: {int(weight*100)}%"

            new_segment = Segment(
                event_id=event_id, name=name, percentage_weight=weight, order_index=order,
                points_per_question=0, total_questions=0
            )
            db.add(new_segment)
            db.commit()
            return True, "Segment added."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def update_segment(self, segment_id, name, weight):
        db = SessionLocal()
        try:
            seg = db.query(Segment).get(segment_id)
            if seg:
                # VALIDATION: Sum of OTHER segments
                current_total = db.query(func.sum(Segment.percentage_weight))\
                    .filter(Segment.event_id == seg.event_id, Segment.id != segment_id).scalar() or 0.0
                
                if (current_total + weight) > 1.0001:
                    return False, f"Total exceeds 100%. Remaining: {int(current_total*100)}% + New: {int(weight*100)}%"

                seg.name = name
                seg.percentage_weight = weight
                db.commit()
                return True, "Updated."
            return False, "Not found."
        finally:
            db.close()

    # ---------------------------------------------------------
    # CRITERIA MANAGEMENT (The Fix You Asked For)
    # ---------------------------------------------------------
    def add_criteria(self, segment_id, name, weight, max_score=100):
        db = SessionLocal()
        try:
            # VALIDATION: Check total weight of criteria in this segment
            current_total = db.query(func.sum(Criteria.weight))\
                .filter(Criteria.segment_id == segment_id).scalar() or 0.0
            
            if (current_total + weight) > 1.0001:
                return False, f"Criteria total exceeds 100%. Current: {int(current_total*100)}%"

            new_crit = Criteria(segment_id=segment_id, name=name, weight=weight, max_score=max_score)
            db.add(new_crit)
            db.commit()
            return True, "Criteria added."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def update_criteria(self, criteria_id, name, weight):
        db = SessionLocal()
        try:
            crit = db.query(Criteria).get(criteria_id)
            if crit:
                # VALIDATION: Sum of OTHER criteria
                current_total = db.query(func.sum(Criteria.weight))\
                    .filter(Criteria.segment_id == crit.segment_id, Criteria.id != criteria_id).scalar() or 0.0
                
                if (current_total + weight) > 1.0001:
                    return False, f"Criteria total exceeds 100%. Current: {int(current_total*100)}%"

                crit.name = name
                crit.weight = weight
                crit.max_score = 100 # Force update to 100 max score
                db.commit()
                return True, "Updated."
            return False, "Not found."
        finally:
            db.close()

    # ---------------------------------------------------------
    # SCORING & UTILS
    # ---------------------------------------------------------
    def submit_score(self, judge_id, contestant_id, criteria_id, score_value):
        db = SessionLocal()
        try:
            existing_score = db.query(Score).filter(
                Score.judge_id == judge_id,
                Score.contestant_id == contestant_id,
                Score.criteria_id == criteria_id
            ).first()

            if existing_score:
                existing_score.score_value = score_value
            else:
                criteria = db.query(Criteria).get(criteria_id)
                new_score = Score(
                    judge_id=judge_id,
                    contestant_id=contestant_id,
                    criteria_id=criteria_id,
                    segment_id=criteria.segment_id,
                    score_value=score_value
                )
                db.add(new_score)
            
            db.commit()
            return True, "Score saved."
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def get_active_pageants(self):
        db = SessionLocal()
        try:
            return db.query(Event).filter(Event.event_type == "Pageant", Event.status == "Active").all()
        finally:
            db.close()

    def get_event_structure(self, event_id):
        db = SessionLocal()
        structure = []
        try:
            segments = db.query(Segment).filter(Segment.event_id == event_id).order_by(Segment.order_index).all()
            for seg in segments:
                criterias = db.query(Criteria).filter(Criteria.segment_id == seg.id).all()
                structure.append({
                    "segment": seg,
                    "criteria": criterias
                })
            return structure
        finally:
            db.close()

    def get_judge_scores(self, judge_id, contestant_id):
        db = SessionLocal()
        scores_map = {}
        try:
            scores = db.query(Score).filter(
                Score.judge_id == judge_id, 
                Score.contestant_id == contestant_id
            ).all()
            
            for s in scores:
                if s.criteria_id:
                    scores_map[s.criteria_id] = s.score_value
            return scores_map
        finally:
            db.close()
            
    def calculate_standing(self, event_id):
        db = SessionLocal()
        results = []
        try:
            contestants = db.query(Contestant).filter(Contestant.event_id == event_id).all()
            segments = db.query(Segment).filter(Segment.event_id == event_id).all()

            for c in contestants:
                total_event_score = 0.0
                
                for s in segments:
                    segment_score = 0.0
                    criterias = db.query(Criteria).filter(Criteria.segment_id == s.id).all()
                    
                    for crit in criterias:
                        avg_score = db.query(func.avg(Score.score_value))\
                            .filter(Score.contestant_id == c.id, Score.criteria_id == crit.id)\
                            .scalar() or 0.0
                        # Calculate weighted score for this criteria
                        segment_score += (avg_score * crit.weight)
                    
                    # Add weighted segment score to total
                    total_event_score += (segment_score * s.percentage_weight)
                
                results.append({
                    "contestant_id": c.id,
                    "name": c.name,
                    "candidate_number": c.candidate_number,
                    "total_score": round(total_event_score, 2)
                })

            results.sort(key=lambda x: x['total_score'], reverse=True)
            return results
        finally:
            db.close()

    # --- ACTIVE SEGMENT CONTROL ---
    
    def set_active_segment(self, event_id, segment_id):
        db = SessionLocal()
        try:
            segments = db.query(Segment).filter(Segment.event_id == event_id).all()
            for seg in segments:
                seg.is_active = False
            
            if segment_id:
                target = db.query(Segment).get(segment_id)
                if target:
                    target.is_active = True
                    msg = f"Segment '{target.name}' is now ACTIVE."
                else:
                    msg = "Segment not found."
            else:
                msg = "All segments deactivated."

            db.commit()
            return True, msg
        except Exception as e:
            return False, str(e)
        finally:
            db.close()

    def get_active_segment(self, event_id):
        db = SessionLocal()
        try:
            return db.query(Segment).filter(
                Segment.event_id == event_id, 
                Segment.is_active == True
            ).first()
        finally:
            db.close()