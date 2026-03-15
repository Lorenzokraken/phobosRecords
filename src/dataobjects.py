from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


@dataclass
class Artist:
    """Data class for artists table."""
    name: str
    royalty_pct: float
    advance_paid: float = 0
    advance_pending: float = 0
    is_front_artist: bool = False
    artist_image: str = ''
    main_genre: str = ''
    work_type: str = ''
    loaded_at: Optional[datetime] = None


@dataclass
class Work:
    """Data class for works table."""
    artist_id: int
    title: str
    secondary_artists_id: str = ''
    work_cover: str = ''
    genre: List[str] = field(default_factory=list)
    bpm: int = 0
    iswc: str = ''
    song_key: str = ''
    release_date: Optional[date] = None
    duration: int = 0
    quota_id: Optional[int] = None
    loaded_at: Optional[datetime] = None


@dataclass
class Transaction:
    """Data class for transactions table."""
    work_id: int
    period: date
    gross_rev: float
    source: str
    platform_fee: Optional[float] = None
    distr_cost: Optional[float] = None
    is_artist_paid: bool = False
    purchase_month: str = ''
    platform: str = ''
    territory: str = ''
    streaming_source: str = ''
    loaded_at: Optional[datetime] = None


@dataclass
class Quota:
    """Data class for quotas table."""
    work_id: int
    artist_id: int
    quota_pct: float
    loaded_at: Optional[datetime] = None
