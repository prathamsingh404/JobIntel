from typing import Dict, Any, List, Optional
from app.classifier.skill_extractor import SkillExtractor
from app.services.vector_service import VectorService
from app.models.database import CleanedJob

class ResumeMatcher:
    """Matches uploaded candidate resumes against clean job listings in JobIntel V2."""

    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.vector_service = VectorService()

    async def match_resume_to_job(self, resume_text: str, job: CleanedJob) -> Dict[str, Any]:
        """Calculates candidate compatibility, highlighting skill gaps and generating roadmaps."""
        # 1. Extract resume skills
        resume_skills_dict = await self.skill_extractor.extract_skills_llm(resume_text)
        
        # Flatten skills
        resume_skills = []
        for cat_skills in resume_skills_dict.values():
            resume_skills.extend(cat_skills)
        resume_skills = sorted(list(set(resume_skills)))

        # 2. Extract job skills
        job_skills_raw = job.skills or ""
        job_skills = [s.strip() for s in job_skills_raw.split(",") if s.strip()]
        if not job_skills:
            # Fallback to extract from description text
            job_skills = self.skill_extractor.extract_skills_regex(job.clean_description)

        # 3. Find matches and gaps
        matched_skills = [s for s in job_skills if s in resume_skills]
        missing_skills = [s for s in job_skills if s not in resume_skills]

        # 4. Generate Semantic Similarity Score
        emb_res = self.vector_service.get_embedding(resume_text)
        emb_job = self.vector_service.get_embedding(job.clean_description)
        
        # Simple dot product
        import numpy as np
        query_vector = np.array(emb_res)
        cand_vector = np.array(emb_job)
        dot_product = np.dot(query_vector, cand_vector)
        norm_q = np.linalg.norm(query_vector)
        norm_c = np.linalg.norm(cand_vector)
        
        semantic_sim = 0.0
        if norm_q > 0 and norm_c > 0:
            semantic_sim = float(dot_product / (norm_q * norm_c))

        # 5. Compute compatibility score (weighted combination)
        skill_weight = 0.6
        semantic_weight = 0.4
        
        skill_score = 100.0
        if job_skills:
            skill_score = (len(matched_skills) / len(job_skills)) * 100.0
            
        match_score = (skill_score * skill_weight) + ((semantic_sim * 100.0) * semantic_weight)
        match_score = min(100.0, max(0.0, round(match_score, 1)))

        # 6. Generate learning roadmap and suggestions
        roadmap = []
        for idx, skill in enumerate(missing_skills):
            roadmap.append({
                "step": idx + 1,
                "skill": skill,
                "action": f"Study {skill} core concepts and build a mini-project.",
                "resources": f"Search for documentation or tutorials on {skill}."
            })

        # Strengths & Weaknesses
        strengths = matched_skills[:5]
        if not strengths:
            strengths = ["Technical background"]
            
        weaknesses = missing_skills[:5]
        if not weaknesses:
            weaknesses = ["No obvious missing technical skills found!"]

        return {
            "match_score": match_score,
            "semantic_similarity": round(semantic_sim * 100, 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "roadmap": roadmap,
            "improvement_suggestions": [
                f"Add these missing keywords directly to your resume profile: {', '.join(missing_skills[:3])}" if missing_skills else "Your resume is highly optimized for this job description!"
            ]
        }
