from datetime import datetime
from typing import List
import re


class CronParser:
    """Simple cron expression parser"""
    
    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field (minute, hour, etc.)"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = []
        
        # Handle comma-separated values
        for part in field.split(','):
            part = part.strip()
            
            # Handle ranges (e.g., "1-5")
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1))
            
            # Handle step values (e.g., "*/5" or "0-30/5")
            elif '/' in part:
                range_part, step_part = part.split('/')
                step = int(step_part)
                
                if range_part == '*':
                    start, end = min_val, max_val
                elif '-' in range_part:
                    start, end = map(int, range_part.split('-'))
                else:
                    start = end = int(range_part)
                
                values.extend(range(start, end + 1, step))
            
            # Handle single values
            else:
                values.append(int(part))
        
        # Filter values within valid range
        return [v for v in values if min_val <= v <= max_val]
    
    @classmethod
    def parse_cron(cls, cron_expr: str) -> dict:
        """Parse a cron expression into its components"""
        parts = cron_expr.strip().split()
        
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 fields: minute hour day month weekday")
        
        minute_str, hour_str, day_str, month_str, weekday_str = parts
        
        return {
            'minutes': cls.parse_field(minute_str, 0, 59),
            'hours': cls.parse_field(hour_str, 0, 23),
            'days': cls.parse_field(day_str, 1, 31),
            'months': cls.parse_field(month_str, 1, 12),
            'weekdays': cls.parse_field(weekday_str, 0, 6)  # 0 = Sunday
        }
    
    @staticmethod
    def should_run(cron_expr: str, check_time: datetime = None) -> bool:
        """Check if a cron job should run at the given time"""
        if check_time is None:
            check_time = datetime.now()
        
        try:
            cron_parts = CronParser.parse_cron(cron_expr)
            
            # Check each component
            if check_time.minute not in cron_parts['minutes']:
                return False
            
            if check_time.hour not in cron_parts['hours']:
                return False
            
            if check_time.day not in cron_parts['days']:
                return False
            
            if check_time.month not in cron_parts['months']:
                return False
            
            # Check weekday (0 = Sunday)
            weekday = check_time.weekday()
            # Convert Python weekday (0=Monday) to cron weekday (0=Sunday)
            cron_weekday = (weekday + 1) % 7
            
            if cron_weekday not in cron_parts['weekdays']:
                return False
            
            return True
            
        except Exception:
            # If parsing fails, don't run
            return False


def should_run_now(cron_expr: str) -> bool:
    """Check if a cron job should run right now"""
    return CronParser.should_run(cron_expr)


def validate_cron_expression(cron_expr: str) -> bool:
    """Validate a cron expression"""
    try:
        CronParser.parse_cron(cron_expr)
        return True
    except Exception:
        return False


def get_next_run_time(cron_expr: str, from_time: datetime = None) -> datetime:
    """Get the next time a cron job will run (approximate)"""
    if from_time is None:
        from_time = datetime.now()
    
    # This is a simplified implementation
    # For production, consider using a proper cron library like croniter
    
    try:
        cron_parts = CronParser.parse_cron(cron_expr)
        
        from datetime import timedelta
        # Start from the next minute
        next_time = from_time.replace(second=0, microsecond=0)
        next_time = next_time + timedelta(minutes=1)
        
        # Simple search for next valid time (up to 1 year)
        for _ in range(525600):  # minutes in a year
            if CronParser.should_run(cron_expr, next_time):
                return next_time
            next_time += timedelta(minutes=1)
        
        # If no valid time found, return far future
        return from_time + timedelta(days=365)
        
    except Exception:
        # If parsing fails, return far future
        return from_time + timedelta(days=365)


# Common cron expressions for easy reference
COMMON_SCHEDULES = {
    'every_minute': '* * * * *',
    'every_5_minutes': '*/5 * * * *',
    'every_15_minutes': '*/15 * * * *',
    'every_30_minutes': '*/30 * * * *',
    'hourly': '0 * * * *',
    'daily': '0 0 * * *',
    'daily_9am': '0 9 * * *',
    'weekly': '0 0 * * 0',
    'monthly': '0 0 1 * *',
}