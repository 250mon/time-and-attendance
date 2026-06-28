핵심은 **회계연도 기준 연차 계산**과 **입사일 기준 법정 최소 연차 계산**을 분리하고, 두 값을 비교해서 부족분을 `legal_adjustment`로 보정하는 구조입니다.

근로기준법 제60조상 기본 규칙은 ① 1년간 80% 이상 출근 시 15일, ② 1년 미만 또는 1년간 80% 미만 출근 시 1개월 개근마다 1일, ③ 3년 이상 계속근로 시 최초 1년 초과 계속근로연수 매 2년마다 1일 가산, ④ 총 25일 한도입니다. ([법제처 웹사이트][1])
회계연도 기준 일괄부여는 가능하지만, 퇴직 시점에서 입사일 기준으로 산정한 휴가일수보다 적으면 부족분을 정산해야 한다는 행정해석이 있습니다. ([세무사신문][2])
또한 정확히 1년만 근무하고 다음 날 근로관계가 없는 경우에는 15일 연차가 별도로 발생하지 않는다는 대법원 판례 흐름이 있으므로, 퇴사일 처리가 중요합니다. ([scourt.go.kr][3])

---

## 1. 구현할 연차 규칙

### A. 입사일 기준 법정 최소 연차

```text
1년 미만:
- 입사 후 매 1개월 개근 시 1일 발생
- 최대 11일

1년 도달일:
- 직전 1년간 80% 이상 출근 시 15일 발생

3년 이상:
- 15일 + floor((만근속연수 - 1) / 2)
- 최대 25일
```

예:

```text
만 1년: 15일
만 2년: 15일
만 3년: 16일
만 4년: 16일
만 5년: 17일
...
최대 25일
```

---

### B. 회계연도 기준 일괄부여

예를 들어 회계연도가 매년 1월 1일 시작이라면:

```text
입사 첫해:
- 1년 미만 월차는 별도로 계속 발생

입사 다음 해 1월 1일:
- 전년도 근속기간 비례 연차 부여
- 예: 2025-07-01 입사
  → 2026-01-01에 15 × 184 / 365 = 약 7.56일

이후 매년 1월 1일:
- 해당 시점의 만근속연수 기준 정규 연차 부여
```

---

### C. 보정 방식

두 가지 방식이 있습니다.

#### 1) 퇴사 시 정산 방식

회계연도 기준으로 운영하다가, 퇴사 시점에만 비교합니다.

```text
입사일 기준 법정 최소 발생분
- 회계연도 기준 실제 부여분
= 부족분

부족분이 있으면 연차수당으로 정산
```

이 방식은 행정해석에 가장 직접적으로 맞는 방식입니다.

#### 2) 1년 도달일 즉시 보정 방식

근로자가 계속 재직 중이어도 입사 1년 도달일에 부족분을 추가 부여합니다.

```text
2025-07-01 입사
2026-07-01 입사 1년 도달

입사일 기준 법정 최소:
- 월차 11일 + 정규연차 15일 = 26일

회계연도 기준 이미 부여:
- 월차 11일 + 2026-01-01 비례연차 7.56일 = 18.56일

부족분:
- 26 - 18.56 = 7.44일

따라서 2026-07-01에 legal_adjustment 7.44일 추가
```

이 방식은 근로자에게 더 명확하고 분쟁 가능성이 낮지만, 다음 회계연도 정기 부여분과의 중복·초과 부여를 회사 규정으로 명확히 해야 합니다.

---

## 2. 반드시 고려해야 할 에지 케이스

| 에지 케이스                    | 처리 원칙                                                    |
| ------------------------------ | ------------------------------------------------------------ |
| 입사일이 1월 1일               | 다음 해 1월 1일에 바로 정규 15일 발생                        |
| 입사일이 7월 1일               | 다음 해 1월 1일 비례연차, 7월 1일 입사일 기준 보정 이슈 발생 |
| 정확히 1년만 근무하고 퇴사     | 다음 날 근로관계가 없으면 15일 정규연차 미발생 가능          |
| 1년 + 1일 이상 근무            | 1년 도달 정규연차 15일 발생 가능                             |
| 회계연도 비례분 소수점         | 회사 규정 필요: 소수점 유지, 반올림, 올림, 0.5일 단위 등     |
| 윤년                           | 365가 아니라 해당 회계연도 실제 일수 365/366 사용 권장       |
| 2월 29일 입사자                | 비윤년 기념일을 2월 28일로 볼지 3월 1일로 볼지 정책 필요     |
| 출근율 80% 미만                | 15일 정규연차 대신 월 개근 1일 기준으로 계산 필요            |
| 휴직·산재·출산휴가·육아휴직    | 출근 간주 여부가 달라질 수 있으므로 별도 근태 모듈 필요      |
| 사용 연차                      | 발생 계산과 사용 차감은 별도 ledger로 관리                   |
| 연차 소멸·사용촉진             | 발생 로직과 별도 모듈로 관리                                 |
| 주 15시간 미만 초단시간 근로자 | 연차 적용 여부 별도 판정 필요                                |

---

## 3. 파이썬 코드

아래 코드는 **발생 연차 ledger**를 계산하는 핵심 로직입니다.

지원하는 것:

```text
- 입사일 기준 법정 최소 연차 계산
- 회계연도 기준 일괄부여 계산
- 첫 회계연도 비례연차 계산
- 입사 1년 도달 보정 계산
- 퇴사 시 정산 계산
- 1월 1일 외 다른 회계연도 시작일 지원
- 윤년 denominator 반영
- 소수점 처리 정책 지원
```

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import calendar
import math
from typing import Literal, Optional


RoundingPolicy = Literal["none", "floor", "ceil", "half_up", "round_2"]
AdjustmentMode = Literal["anniversary_top_up", "termination_only", "none"]


@dataclass(frozen=True)
class LeaveEvent:
    date: date
    days: float
    event_type: str
    basis: str
    note: str = ""


def parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def add_months(d: date, months: int) -> date:
    """
    월 단위 기념일 계산.
    예: 2025-01-31 + 1개월 = 2025-02-28
    """
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, days_in_month(y, m))
    return date(y, m, day)


def add_years(d: date, years: int) -> date:
    """
    연 단위 기념일 계산.
    2월 29일 입사자의 비윤년 기념일은 2월 28일로 처리.
    회사 규정에 따라 3월 1일로 바꿀 수도 있음.
    """
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def completed_years(start: date, as_of: date) -> int:
    """
    as_of 날짜 기준 만 근속연수.
    """
    years = as_of.year - start.year
    if add_years(start, years) > as_of:
        years -= 1
    return max(0, years)


def regular_annual_leave(completed_service_years: int) -> int:
    """
    입사일 기준 만근속연수별 정규 연차.

    만 1년: 15일
    만 2년: 15일
    만 3년: 16일
    만 4년: 16일
    만 5년: 17일
    ...
    최대 25일
    """
    if completed_service_years < 1:
        return 0

    bonus = max(0, (completed_service_years - 1) // 2)
    return min(15 + bonus, 25)


def round_days(value: float, rounding: RoundingPolicy) -> float:
    """
    회계연도 비례연차 소수점 처리.
    법정 최소보다 불리하면 안 되므로 최종적으로는 legal_adjustment와 함께 검토해야 함.
    """
    if rounding == "none":
        return value
    if rounding == "floor":
        return float(math.floor(value))
    if rounding == "ceil":
        return float(math.ceil(value))
    if rounding == "half_up":
        return math.ceil(value * 2) / 2
    if rounding == "round_2":
        return round(value, 2)

    raise ValueError(f"Unsupported rounding policy: {rounding}")


def fiscal_start_for_year(
    year: int,
    fiscal_start_month: int,
    fiscal_start_day: int,
) -> date:
    """
    특정 연도의 회계연도 시작일.
    예: fiscal_start_month=1, fiscal_start_day=1 → 매년 1월 1일
    """
    day = min(fiscal_start_day, days_in_month(year, fiscal_start_month))
    return date(year, fiscal_start_month, day)


def fiscal_starts_after_until(
    start_exclusive: date,
    end_inclusive: date,
    fiscal_start_month: int,
    fiscal_start_day: int,
):
    """
    start_exclusive 이후, end_inclusive 이하의 회계연도 시작일들을 순회.
    """
    for year in range(start_exclusive.year, end_inclusive.year + 2):
        fs = fiscal_start_for_year(year, fiscal_start_month, fiscal_start_day)
        if start_exclusive < fs <= end_inclusive:
            yield fs


def previous_fiscal_start(
    fiscal_start: date,
    fiscal_start_month: int,
    fiscal_start_day: int,
) -> date:
    return fiscal_start_for_year(
        fiscal_start.year - 1,
        fiscal_start_month,
        fiscal_start_day,
    )


def cumulative_days(events: list[LeaveEvent], on_or_before: date) -> float:
    return sum(e.days for e in events if e.date <= on_or_before)


def serialize_events(events: list[LeaveEvent]) -> list[dict]:
    return [
        {
            "date": e.date.isoformat(),
            "days": round(e.days, 4),
            "event_type": e.event_type,
            "basis": e.basis,
            "note": e.note,
        }
        for e in sorted(events, key=lambda x: (x.date, x.basis, x.event_type))
    ]


def legal_minimum_events(
    hire_date: date,
    effective_as_of: date,
    *,
    assume_full_attendance: bool = True,
) -> list[LeaveEvent]:
    """
    입사일 기준 법정 최소 발생 연차.

    단순화 가정:
    - 1년 미만 월차는 모두 개근했다고 가정
    - 1년 단위 출근율은 80% 이상이라고 가정
    - 휴직, 결근, 출근간주 기간은 별도 근태 모듈에서 처리

    실무에서는 assume_full_attendance=False인 경우
    월별 개근 여부와 연간 출근율 데이터를 연결해야 함.
    """
    events: list[LeaveEvent] = []

    if effective_as_of < hire_date:
        return events

    # 1년 미만 월차: 매 1개월 개근 시 1일, 최대 11일
    for month_index in range(1, 12):
        grant_date = add_months(hire_date, month_index)
        if grant_date <= effective_as_of:
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=1.0,
                    event_type="monthly_under_one_year",
                    basis="legal_minimum",
                    note=f"{month_index} complete month(s) after hire",
                )
            )

    # 매년 입사일 기준 정규 연차
    service_years = completed_years(hire_date, effective_as_of)

    for year in range(1, service_years + 1):
        grant_date = add_years(hire_date, year)

        if grant_date > effective_as_of:
            continue

        if assume_full_attendance:
            days = float(regular_annual_leave(year))
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=days,
                    event_type="annual_anniversary",
                    basis="legal_minimum",
                    note=f"{year} completed service year(s)",
                )
            )
        else:
            # 출근율 80% 미만 또는 출근자료 불명확한 경우
            # 이 코드에서는 자동 산정하지 않고 근태 모듈 연결을 요구.
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=0.0,
                    event_type="annual_attendance_unknown",
                    basis="legal_minimum",
                    note="Requires annual attendance rate and monthly perfect-attendance records",
                )
            )

    return sorted(events, key=lambda e: (e.date, e.event_type))


def first_fiscal_prorated_leave(
    hire_date: date,
    grant_date: date,
    *,
    fiscal_start_month: int,
    fiscal_start_day: int,
) -> float:
    """
    첫 회계연도 비례연차.

    예:
    - 입사일: 2025-07-01
    - 회계연도 시작: 1월 1일
    - 부여일: 2026-01-01
    - 전년도 근속일수: 184일
    - 비례연차: 15 × 184 / 365 = 7.5616...
    """
    prev_start = previous_fiscal_start(
        grant_date,
        fiscal_start_month,
        fiscal_start_day,
    )
    prev_end = grant_date

    service_start = max(hire_date, prev_start)
    service_days = max(0, (prev_end - service_start).days)
    period_days = (prev_end - prev_start).days

    if service_days <= 0 or period_days <= 0:
        return 0.0

    return 15.0 * service_days / period_days


def fiscal_policy_events(
    hire_date: date,
    effective_as_of: date,
    *,
    fiscal_start_month: int = 1,
    fiscal_start_day: int = 1,
    fiscal_rounding: RoundingPolicy = "round_2",
    assume_full_attendance: bool = True,
) -> list[LeaveEvent]:
    """
    회계연도 기준 회사 부여 연차.

    구성:
    1. 1년 미만 월차는 회계연도 방식에서도 별도로 발생
    2. 입사 후 첫 회계연도 시작일이 1년 도달 전이면 비례연차 부여
    3. 이후 회계연도 시작일에는 정규 연차 부여
    """
    events: list[LeaveEvent] = []

    if effective_as_of < hire_date:
        return events

    first_anniversary = add_years(hire_date, 1)

    # 1년 미만 월차
    monthly_cutoff = min(effective_as_of, first_anniversary)

    for month_index in range(1, 12):
        grant_date = add_months(hire_date, month_index)
        if grant_date <= monthly_cutoff:
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=1.0,
                    event_type="monthly_under_one_year",
                    basis="fiscal_policy",
                    note=f"{month_index} complete month(s) after hire",
                )
            )

    # 회계연도 시작일 부여분
    for grant_date in fiscal_starts_after_until(
        hire_date,
        effective_as_of,
        fiscal_start_month,
        fiscal_start_day,
    ):
        if grant_date < first_anniversary:
            raw_days = first_fiscal_prorated_leave(
                hire_date,
                grant_date,
                fiscal_start_month=fiscal_start_month,
                fiscal_start_day=fiscal_start_day,
            )
            days = round_days(raw_days, fiscal_rounding)

            if days > 0:
                events.append(
                    LeaveEvent(
                        date=grant_date,
                        days=days,
                        event_type="fiscal_prorated_first_year",
                        basis="fiscal_policy",
                        note=f"raw={raw_days:.6f}",
                    )
                )

        else:
            service_years_at_fiscal_start = completed_years(hire_date, grant_date)

            if assume_full_attendance:
                days = float(regular_annual_leave(service_years_at_fiscal_start))
                if days > 0:
                    events.append(
                        LeaveEvent(
                            date=grant_date,
                            days=days,
                            event_type="fiscal_regular_annual",
                            basis="fiscal_policy",
                            note=f"{service_years_at_fiscal_start} completed service year(s) at fiscal start",
                        )
                    )
            else:
                events.append(
                    LeaveEvent(
                        date=grant_date,
                        days=0.0,
                        event_type="fiscal_attendance_unknown",
                        basis="fiscal_policy",
                        note="Requires attendance records",
                    )
                )

    return sorted(events, key=lambda e: (e.date, e.event_type))


def legal_adjustment_events(
    legal_events: list[LeaveEvent],
    fiscal_events: list[LeaveEvent],
    effective_as_of: date,
    *,
    mode: AdjustmentMode = "anniversary_top_up",
    adjustment_date: Optional[date] = None,
) -> list[LeaveEvent]:
    """
    회계연도 기준 부여분이 입사일 기준 법정 최소분보다 적을 때 보정 이벤트 생성.

    mode:
    - "anniversary_top_up":
        입사일 기준 법정 발생일마다 부족분을 즉시 추가 부여.
        근로자에게 가장 명확하나, 회사 입장에서는 다소 관대한 방식.

    - "termination_only":
        퇴사일에만 부족분 정산.
        회계연도 기준 운영에서 흔히 사용하는 방식.

    - "none":
        보정 이벤트 생성하지 않음.
        단, summary에서 shortage_if_settled_now_without_adjustment 확인 가능.
    """
    if mode == "none":
        return []

    adjustments: list[LeaveEvent] = []

    if mode == "termination_only":
        if adjustment_date is None:
            return []
        check_dates = [adjustment_date]
    else:
        check_dates = sorted(
            {e.date for e in legal_events if e.date <= effective_as_of}
            | {effective_as_of}
        )

    for check_date in check_dates:
        legal_total = cumulative_days(legal_events, check_date)
        fiscal_total = cumulative_days(fiscal_events, check_date)
        adjustment_total = cumulative_days(adjustments, check_date)

        shortage = legal_total - fiscal_total - adjustment_total

        if shortage > 1e-9:
            adjustments.append(
                LeaveEvent(
                    date=check_date,
                    days=shortage,
                    event_type="legal_adjustment",
                    basis="adjustment",
                    note="Top-up so fiscal-year operation is not below legal minimum",
                )
            )

    return adjustments


def calculate_annual_leave(
    hire_date: str | date,
    as_of: str | date,
    *,
    termination_date: str | date | None = None,
    fiscal_start_month: int = 1,
    fiscal_start_day: int = 1,
    fiscal_rounding: RoundingPolicy = "round_2",
    adjustment_mode: AdjustmentMode = "anniversary_top_up",
    assume_full_attendance: bool = True,
) -> dict:
    """
    연차 발생 계산 메인 함수.

    Parameters
    ----------
    hire_date:
        입사일.

    as_of:
        계산 기준일.

    termination_date:
        퇴사일. 이 코드에서는 '마지막으로 근로관계가 존재하는 날'로 정의.
        예:
        - 2026-06-30 퇴사: 2026-07-01 발생 연차 없음
        - 2026-07-01 퇴사: 2026-07-01 발생 연차 있음

    adjustment_mode:
        - anniversary_top_up: 입사일 기준 부족분 즉시 보정
        - termination_only: 퇴사 시에만 부족분 정산
        - none: 보정 없음, 부족분만 계산
    """
    hire = parse_date(hire_date)
    calc_as_of = parse_date(as_of)
    termination = parse_date(termination_date) if termination_date else None

    if calc_as_of < hire:
        raise ValueError("as_of cannot be earlier than hire_date.")

    if termination is not None and termination < hire:
        raise ValueError("termination_date cannot be earlier than hire_date.")

    effective_as_of = min(calc_as_of, termination) if termination else calc_as_of

    legal = legal_minimum_events(
        hire,
        effective_as_of,
        assume_full_attendance=assume_full_attendance,
    )

    fiscal = fiscal_policy_events(
        hire,
        effective_as_of,
        fiscal_start_month=fiscal_start_month,
        fiscal_start_day=fiscal_start_day,
        fiscal_rounding=fiscal_rounding,
        assume_full_attendance=assume_full_attendance,
    )

    adjustment_date = termination if termination and termination <= calc_as_of else None

    adjustments = legal_adjustment_events(
        legal,
        fiscal,
        effective_as_of,
        mode=adjustment_mode,
        adjustment_date=adjustment_date,
    )

    legal_total = cumulative_days(legal, effective_as_of)
    fiscal_total = cumulative_days(fiscal, effective_as_of)
    adjustment_total = cumulative_days(adjustments, effective_as_of)
    total_after_adjustment = fiscal_total + adjustment_total

    return {
        "hire_date": hire.isoformat(),
        "as_of": calc_as_of.isoformat(),
        "effective_as_of": effective_as_of.isoformat(),
        "termination_date": termination.isoformat() if termination else None,
        "fiscal_year_start": f"{fiscal_start_month:02d}-{fiscal_start_day:02d}",
        "assumptions": {
            "full_attendance": assume_full_attendance,
            "termination_date_is_last_employed_day_inclusive": True,
            "feb_29_anniversary_policy": "Feb 28 in non-leap years",
            "fiscal_proration_denominator": "actual days in prior fiscal year",
            "fiscal_rounding": fiscal_rounding,
            "adjustment_mode": adjustment_mode,
        },
        "summary": {
            "legal_minimum_total": round(legal_total, 4),
            "raw_fiscal_policy_total": round(fiscal_total, 4),
            "legal_adjustment_total": round(adjustment_total, 4),
            "total_after_adjustment": round(total_after_adjustment, 4),
            "shortage_if_settled_now_without_adjustment": round(
                max(0.0, legal_total - fiscal_total),
                4,
            ),
        },
        "legal_minimum_events": serialize_events(legal),
        "fiscal_policy_events": serialize_events(fiscal),
        "adjustment_events": serialize_events(adjustments),
    }
```

---

## 4. 사용 예시

### 예시 1: 2025-07-01 입사, 2026-07-01 기준

```python
result = calculate_annual_leave(
    hire_date="2025-07-01",
    as_of="2026-07-01",
    fiscal_start_month=1,
    fiscal_start_day=1,
    fiscal_rounding="none",
    adjustment_mode="anniversary_top_up",
)

print(result["summary"])
print(result["adjustment_events"])
```

예상 결과:

```python
{
    "legal_minimum_total": 26.0,
    "raw_fiscal_policy_total": 18.5616,
    "legal_adjustment_total": 7.4384,
    "total_after_adjustment": 26.0,
    "shortage_if_settled_now_without_adjustment": 7.4384,
}
```

의미:

```text
입사일 기준 법정 최소:
- 1년 미만 월차 11일
- 1년 도달 정규연차 15일
= 총 26일

회계연도 기준 이미 부여:
- 월차 11일
- 2026-01-01 비례연차 7.5616일
= 총 18.5616일

부족분:
- 7.4384일

따라서 2026-07-01에 legal_adjustment 7.4384일 추가
```

---

### 예시 2: 같은 직원이 2026-06-30까지만 근무하고 퇴사

```python
result = calculate_annual_leave(
    hire_date="2025-07-01",
    as_of="2026-06-30",
    termination_date="2026-06-30",
    fiscal_rounding="none",
    adjustment_mode="termination_only",
)

print(result["summary"])
```

예상 의미:

```text
2026-07-01에 근로관계가 없으므로 1년 도달 15일은 발생하지 않음.
입사일 기준 법정 최소는 월차 11일.
회계연도 기준으로는 월차 11일 + 비례연차 7.56일이 이미 부여되어 있으므로 부족분 없음.
```

---

### 예시 3: 같은 직원이 2026-10-01 퇴사

```python
result = calculate_annual_leave(
    hire_date="2025-07-01",
    as_of="2026-10-01",
    termination_date="2026-10-01",
    fiscal_rounding="none",
    adjustment_mode="termination_only",
)

print(result["summary"])
print(result["adjustment_events"])
```

예상 의미:

```text
2026-07-01에 1년 도달 연차 15일이 발생.
하지만 2027-01-01 정기 회계연도 부여 전 퇴사.
따라서 퇴사 시점에 부족분 7.4384일 정산 필요.
```

---

## 5. 실무 시스템 설계 권장안

DB에는 “잔여 연차 숫자 하나”만 저장하지 말고, 반드시 ledger로 저장하는 것이 좋습니다.

```text
leave_entitlements
- id
- employee_id
- event_date
- days
- event_type
  - monthly_under_one_year
  - fiscal_prorated_first_year
  - fiscal_regular_annual
  - legal_adjustment
  - manual_adjustment
- basis
  - legal_minimum
  - fiscal_policy
  - adjustment
- expires_at
- note
- created_at
```

사용 내역은 별도 테이블로 분리합니다.

```text
leave_usages
- id
- employee_id
- leave_date
- days
- approval_status
- reason
- created_at
```

최종 잔여 연차는 저장값이 아니라 계산값으로 두는 것이 안전합니다.

```text
잔여 연차 =
발생/부여 연차
+ 보정 연차
- 사용 연차
- 소멸 연차
```

## 결론

연차 시스템의 안전한 계산 구조는 다음입니다.

```text
1. 입사일 기준 법정 최소 연차를 계산한다.
2. 회계연도 기준 회사 부여 연차를 계산한다.
3. 둘을 비교한다.
4. 부족분이 있으면:
   - 재직 중 즉시 보정하거나
   - 퇴사 시 정산한다.
5. 발생, 사용, 소멸, 정산을 ledger로 분리한다.
```

병·의원 직원 근태관리 시스템에 넣는다면 기본값은 다음을 권합니다.

```text
회계연도 기준: 1월 1일
소수점 처리: 0.5일 단위 올림 또는 소수점 유지
보정 방식: termination_only + 퇴사정산 필수
분쟁 예방형 옵션: anniversary_top_up
```

[1]: https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1001516877&utm_source=chatgpt.com "근로기준법"
[2]: https://webzine.kacta.or.kr/news/articleView.html?idxno=21917&utm_source=chatgpt.com "퇴사 시 연차휴가 입사일 기준으로 정산 - 세무사신문"
[3]: https://www.scourt.go.kr/portal/news/NewsViewAction.work?gubun=4&pageIndex=3&searchOption=&searchWord=&seqnum=8782&type=52015&utm_source=chatgpt.com "연차휴가일수 산정방법에 대한 사건[대법원 2022. 9. 7. 선고 ..."
