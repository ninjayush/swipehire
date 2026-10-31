import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.db import init_db, SessionLocal
from app.api.candidates import router as candidates_router
from app.api.companies import router as companies_router
from app.api.jobs import router as jobs_router
from app.api.matches import router as matches_router
from app.models.user import User
from app.models.company import Company, CompanyMember
from app.models.job import JobRole
from app.integrations.crustdata import crustdata_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swipehire.backend")

def seed_demo_data():
    """Seeds demo recruiter, demo company, and candidate for seamless local prototyping."""
    db = SessionLocal()
    try:
        # Check if company already seeded
        existing_company = db.query(Company).filter(Company.name == "Demo Corp").first()
        if not existing_company:
            logger.info("Seeding initial demo company and recruiter...")
            company = Company(
                name="Demo Corp",
                domain="democorp.io",
                enriched_data={"industry": "Technology", "headcount": "50-100", "summary": "AI hiring innovation"}
            )
            db.add(company)
            db.commit()
            db.refresh(company)

            recruiter = User(
                email="recruiter@democorp.io",
                role="recruiter",
                name="Alex Recruiter"
            )
            db.add(recruiter)
            db.commit()
            db.refresh(recruiter)

            membership = CompanyMember(
                company_id=company.id,
                user_id=recruiter.id,
                role="admin"
            )
            db.add(membership)

            # Sample job
            demo_job = JobRole(
                company_id=company.id,
                title="Senior Full-Stack Engineer",
                status="active",
                raw_jd="Looking for Senior Full-Stack Engineer with Python, FastAPI, React experience. 4+ years.",
                requirements={
                    "title": "Senior Full-Stack Engineer",
                    "seniority": "Senior",
                    "min_experience_years": 4.0,
                    "locations": ["San Francisco, CA", "Remote"],
                    "work_modes": ["hybrid", "remote"],
                    "must_have_skills": ["Python", "FastAPI", "React"],
                    "preferred_skills": ["SQLAlchemy", "TypeScript"],
                    "dealbreakers": []
                }
            )
            db.add(demo_job)
            db.commit()
            logger.info("Demo data seeded successfully.")
    except Exception as e:
        logger.warning(f"Demo seeding warning: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed demo fixtures
    init_db()
    seed_demo_data()
    # Check Crustdata client configuration safely
    diag = await crustdata_client.diagnostics()
    logger.info(f"Crustdata initial connectivity probe: {diag.get('status')}")
    yield
    # Shutdown

app = FastAPI(
    title="SwipeHire API",
    description="Backend API and Crustdata integration engine for SwipeHire",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(candidates_router)
app.include_router(companies_router)
app.include_router(jobs_router)
app.include_router(matches_router)

@app.get("/")
def root():
    return {
        "app": "SwipeHire API",
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    diag = await crustdata_client.diagnostics()
    return {
        "status": "healthy",
        "crustdata": diag
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
