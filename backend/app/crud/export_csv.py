"""CSV export for customers and costs — returns StreamingResponse with UTF-8 BOM."""

from __future__ import annotations

import csv
import io

from fastapi.responses import StreamingResponse


def customers_csv(rows: list[dict]) -> StreamingResponse:
    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["姓名", "手机号", "备注", "累计消费", "创建时间"])
    for r in rows:
        writer.writerow([
            r.get("name", ""),
            r.get("phone", ""),
            r.get("note", ""),
            f'{float(r.get("total_amount", 0)):.2f}',
            str(r.get("created_at", ""))[:10] if r.get("created_at") else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=customers.csv"},
    )


def costs_csv(rows: list[dict]) -> StreamingResponse:
    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["日期", "宠物名", "客户名", "服务项目", "金额", "优惠", "支付方式", "备注"])
    for r in rows:
        writer.writerow([
            str(r.get("occurred_on", ""))[:10] if r.get("occurred_on") else "",
            r.get("pet_name", ""),
            r.get("customer_name", ""),
            r.get("category_label", ""),
            f'{float(r.get("amount", 0)):.2f}',
            f'{float(r.get("discount_amount", 0)):.2f}',
            "储值" if r.get("pay_method") == "balance" else "现金",
            r.get("note", ""),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=costs.csv"},
    )