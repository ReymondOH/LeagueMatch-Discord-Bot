import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from .models import Role, StatsResponse
from .repository import aggregate_demo, database_stats

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
logger = logging.getLogger(__name__)


def create_app(*, demo_mode: bool | None = None, supplied_pool=None):
    demo = (os.getenv('DEMO_MODE', 'true').lower() == 'true') if demo_mode is None else demo_mode

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pool = supplied_pool
        if not demo and supplied_pool is None:
            options = dict(min_size=1, max_size=5, command_timeout=15)
            ssl = os.getenv('DB_SSL', 'disable')
            if os.getenv('DATABASE_URL'):
                options['dsn'] = os.environ['DATABASE_URL']
                # Preserve provider SSL query parameters unless explicitly overridden.
                if 'DB_SSL' in os.environ:
                    options['ssl'] = ssl
            else:
                options.update(host=os.getenv('DB_HOST', 'localhost'), port=int(os.getenv('DB_PORT', '5432')),
                    database=os.getenv('DB_NAME', 'leaguematch'), user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', ''), ssl=ssl)
            try:
                app.state.pool = await asyncpg.create_pool(**options)
            except Exception:
                # Do not include connection strings or credentials in HTTP responses.
                logger.error('PostgreSQL connection failed. Check the backend database settings.')
        yield
        if app.state.pool is not None and supplied_pool is None:
            await app.state.pool.close()

    app = FastAPI(title='LeagueMatch API', version='1.0.0', lifespan=lifespan,
                  description='Read-only aggregate statistics from the LeagueMatch collector.')
    origins = [s.strip() for s in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if s.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=['GET'], allow_headers=['Accept', 'Content-Type'])

    @app.get('/api/health')
    async def health(request: Request):
        if demo:
            return {'status': 'ok', 'source': 'demo'}
        pool = request.app.state.pool
        if pool is None:
            raise HTTPException(503, 'Database unavailable')
        try:
            await pool.fetchval('SELECT 1')
        except Exception:
            raise HTTPException(503, 'Database unavailable') from None
        return {'status': 'ok', 'source': 'database'}

    @app.get('/api/stats', response_model=StatsResponse)
    async def stats(request: Request,
                    champion_id: Annotated[int | None, Query(ge=1)] = None,
                    role: Role | None = None,
                    patch: Annotated[str | None, Query(pattern=r'^\d{1,3}\.\d{1,3}$')] = None,
                    page: Annotated[int, Query(ge=1, le=10000)] = 1,
                    page_size: Annotated[int, Query(ge=1, le=50)] = 8):
        params = dict(champion_id=champion_id, role=role.value if role else None, patch=patch,
                      page=page, page_size=page_size)
        if demo:
            return aggregate_demo(**params)
        pool = request.app.state.pool
        if pool is None:
            raise HTTPException(503, 'Database unavailable')
        try:
            return await database_stats(pool, **params)
        except Exception:
            logger.error('Statistics query failed. Verify match_stats exists and the database user has SELECT access.')
            raise HTTPException(503, 'Statistics temporarily unavailable') from None

    return app


app = create_app()
