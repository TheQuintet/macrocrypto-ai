"""Export service for generating data exports in various formats.

This module provides a service class for generating exports in CSV, PNG,
and PDF formats for predictions, correlations, accuracy, and regimes data.
"""

import io
import json
import logging
import csv
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, white, grey, blue, red, green

from app.core.config import settings
from app.services.prediction_service import prediction_service
from app.services.market_service import market_service

logger = logging.getLogger(settings.SERVICE_NAME)


class ExportService:
    """Service for generating data exports in various formats."""

    def __init__(self):
        """Initialize the export service."""
        self.export_dir = Path("./exports")
        self.export_dir.mkdir(exist_ok=True)

    async def generate_export(
        self,
        user_id: int,
        data_type: str,
        format_type: str,
        timeframe: str = "24h",
        symbol: str = "BTC",
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate an export in the specified format.

        Args:
            user_id: The user ID.
            data_type: Type of data to export (predictions, correlations, accuracy, regimes).
            format_type: Format to export (csv, png, pdf).
            timeframe: Timeframe for the data.
            symbol: Trading symbol (default: BTC).
            **kwargs: Additional parameters.

        Returns:
            Dict[str, Any]: Export result with file info.
        """
        try:
            # Fetch data based on type
            data = await self._fetch_data(data_type, symbol, timeframe, **kwargs)

            # Generate file based on format
            if format_type == "csv":
                file_data = self._generate_csv(data, data_type, symbol, timeframe)
                file_extension = "csv"
                content_type = "text/csv"
            elif format_type == "png":
                file_data = await self._generate_png(data, data_type, symbol, timeframe)
                file_extension = "png"
                content_type = "image/png"
            elif format_type == "pdf":
                file_data = await self._generate_pdf(data, data_type, symbol, timeframe)
                file_extension = "pdf"
                content_type = "application/pdf"
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            # Generate filename
            filename = f"{data_type}_{symbol}_{timeframe}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            file_path = self.export_dir / filename

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_data)

            # Get file size
            file_size = file_path.stat().st_size

            logger.info(f"Export generated: {filename} (user={user_id}, size={file_size} bytes)")

            return {
                "file_path": str(file_path),
                "file_name": filename,
                "file_size": file_size,
                "content_type": content_type,
                "data": file_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Export generation failed: {e}")
            raise

    async def _fetch_data(
        self,
        data_type: str,
        symbol: str,
        timeframe: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Fetch data for export based on type.

        Args:
            data_type: Type of data.
            symbol: Trading symbol.
            timeframe: Timeframe.
            **kwargs: Additional parameters.

        Returns:
            Dict[str, Any]: The fetched data.

        Raises:
            ValueError: If data_type is unsupported.
        """
        if data_type == "predictions":
            return await prediction_service.get_predictions(
                symbol=symbol,
                timeframe=timeframe,
                model_type=kwargs.get("model_type", "ensemble"),
            )
        elif data_type == "accuracy":
            return await prediction_service.get_accuracy_metrics(
                symbol=symbol,
                days=kwargs.get("days", 30),
            )
        elif data_type == "correlations":
            return await market_service.get_correlation(
                symbol=symbol,
                window=kwargs.get("window", "30d"),
            )
        elif data_type == "regimes":
            return await market_service.get_regimes(
                symbol=symbol,
                timeframe=timeframe,
            )
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def _generate_csv(self, data: Dict[str, Any], data_type: str, symbol: str, timeframe: str) -> bytes:
        """Generate CSV export.

        Args:
            data: The data to export.
            data_type: Type of data.
            symbol: Trading symbol.
            timeframe: Timeframe.

        Returns:
            bytes: The CSV file content.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header based on data type
        if data_type == "predictions":
            writer.writerow(["Timestamp", "Price", "Lower Bound", "Upper Bound", "Confidence"])
            for pred in data.get("predictions", []):
                writer.writerow([
                    pred.get("timestamp"),
                    pred.get("price"),
                    pred.get("lower_bound"),
                    pred.get("upper_bound"),
                    pred.get("confidence"),
                ])
        elif data_type == "accuracy":
            writer.writerow(["Metric", "Value"])
            for key, value in data.items():
                if key in ["symbol", "days", "timestamp", "cached"]:
                    continue
                if isinstance(value, dict):
                    continue
                writer.writerow([key, value])
        elif data_type == "correlations":
            writer.writerow(["Indicator", "Correlation", "Strength"])
            for indicator, corr_data in data.get("correlations", {}).items():
                writer.writerow([
                    indicator,
                    corr_data.get("value"),
                    corr_data.get("strength"),
                ])
        elif data_type == "regimes":
            writer.writerow(["Regime Type", "Start Date", "End Date", "Duration", "Avg Return", "Max Drawdown"])
            for regime in data.get("regimes", []):
                writer.writerow([
                    regime.get("regime_type"),
                    regime.get("start_date"),
                    regime.get("end_date"),
                    regime.get("duration_days"),
                    regime.get("avg_return"),
                    regime.get("max_drawdown"),
                ])

        return output.getvalue().encode("utf-8")

    async def _generate_png(self, data: Dict[str, Any], data_type: str, symbol: str, timeframe: str) -> bytes:
        """Generate PNG export.

        Args:
            data: The data to export.
            data_type: Type of data.
            symbol: Trading symbol.
            timeframe: Timeframe.

        Returns:
            bytes: The PNG file content.
        """
        plt.figure(figsize=(12, 6))

        if data_type == "predictions":
            self._create_prediction_chart(data, symbol, timeframe)
        elif data_type == "accuracy":
            self._create_accuracy_chart(data)
        elif data_type == "correlations":
            self._create_correlation_chart(data)
        elif data_type == "regimes":
            self._create_regime_chart(data)
        else:
            raise ValueError(f"Unsupported data type for PNG: {data_type}")

        plt.title(f"{symbol} - {data_type.capitalize()} ({timeframe})")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        buf.seek(0)
        return buf.getvalue()

    def _create_prediction_chart(self, data: Dict[str, Any], symbol: str, timeframe: str) -> None:
        """Create prediction chart."""
        predictions = data.get("predictions", [])
        if not predictions:
            plt.text(0.5, 0.5, "No prediction data available", ha="center", va="center", transform=plt.gca().transAxes)
            return

        timestamps = []
        prices = []
        lower_bounds = []
        upper_bounds = []

        for pred in predictions:
            try:
                timestamps.append(pred.get("timestamp", ""))
                prices.append(pred.get("price", 0))
                lower_bounds.append(pred.get("lower_bound", 0))
                upper_bounds.append(pred.get("upper_bound", 0))
            except Exception as e:
                logger.warning(f"Skipping prediction point: {e}")

        x = list(range(len(timestamps)))
        plt.plot(x, prices, "b-", label="Predicted Price", linewidth=2)
        plt.fill_between(x, lower_bounds, upper_bounds, alpha=0.2, color="blue", label="Confidence Band")
        plt.axhline(y=data.get("current_price", 0), color="gray", linestyle="--", label="Current Price")
        plt.xlabel("Time")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.xticks(rotation=45, ha="right")

    def _create_accuracy_chart(self, data: Dict[str, Any]) -> None:
        """Create accuracy chart."""
        metrics = {
            "Accuracy": data.get("overall_accuracy", 0),
            "RMSE": data.get("rmse", 0),
            "MAE": data.get("mae", 0),
        }
        keys = list(metrics.keys())
        values = [float(v) for v in metrics.values()]
        bars = plt.bar(keys, values, color=["green", "orange", "red"])
        plt.ylabel("Score")
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{value:.1f}", ha="center")

    def _create_correlation_chart(self, data: Dict[str, Any]) -> None:
        """Create correlation chart."""
        correlations = data.get("correlations", {})
        if not correlations:
            plt.text(0.5, 0.5, "No correlation data available", ha="center", va="center", transform=plt.gca().transAxes)
            return

        keys = list(correlations.keys())
        values = [corr.get("value", 0) for corr in correlations.values()]
        colors = ["green" if v >= 0 else "red" for v in values]
        plt.bar(keys, values, color=colors)
        plt.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Correlation Coefficient")

    def _create_regime_chart(self, data: Dict[str, Any]) -> None:
        """Create regime chart."""
        regimes = data.get("regimes", [])
        if not regimes:
            plt.text(0.5, 0.5, "No regime data available", ha="center", va="center", transform=plt.gca().transAxes)
            return

        colors = {
            "bull": "green",
            "bear": "red",
            "sideways": "yellow",
            "neutral": "gray",
        }
        for regime in regimes:
            regime_type = regime.get("regime_type", "neutral").lower()
            avg_return = regime.get("avg_return", 0)
            color = colors.get(regime_type, "gray")
            label = f"{regime_type} ({avg_return:.1f}%)"
            plt.bar(regime_type, avg_return, color=color, label=label if regime_type not in plt.gca().get_legend_handles_labels()[1] else "")
        plt.ylabel("Average Return (%)")
        plt.legend()

    async def _generate_pdf(self, data: Dict[str, Any], data_type: str, symbol: str, timeframe: str) -> bytes:
        """Generate PDF export.

        Args:
            data: The data to export.
            data_type: Type of data.
            symbol: Trading symbol.
            timeframe: Timeframe.

        Returns:
            bytes: The PDF file content.
        """
        # First generate PNG chart
        png_data = await self._generate_png(data, data_type, symbol, timeframe)

        # Create PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"MacroCrypto AI - {symbol} {data_type.capitalize()} Export")

        # Subtitle
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(50, height - 90, f"Timeframe: {timeframe}")

        # Chart
        img = ImageReader(io.BytesIO(png_data))
        c.drawImage(img, 50, height - 450, width=500, height=350)

        # Summary
        c.setFont("Helvetica", 10)
        y_pos = height - 500
        summary = self._get_summary_text(data, data_type, symbol)
        for line in summary:
            c.drawString(50, y_pos, line)
            y_pos -= 15
            if y_pos < 50:
                c.showPage()
                y_pos = height - 50
                c.setFont("Helvetica", 10)

        c.save()
        buf.seek(0)
        return buf.getvalue()

    def _get_summary_text(self, data: Dict[str, Any], data_type: str, symbol: str) -> List[str]:
        """Get summary text for PDF."""
        lines = [f"Summary Report: {symbol} {data_type.capitalize()}"]
        lines.append("")

        if data_type == "predictions":
            current_price = data.get("current_price", 0)
            change_percent = data.get("change_percent", 0)
            lines.append(f"Current Price: ${current_price:,.2f}")
            lines.append(f"Change: {change_percent:+.2f}%")
            lines.append(f"Predictions Count: {len(data.get('predictions', []))}")
            if data.get("predictions"):
                last_pred = data["predictions"][-1]
                lines.append(f"Last Prediction: ${last_pred.get('price', 0):,.2f}")

        elif data_type == "accuracy":
            lines.append(f"Overall Accuracy: {data.get('overall_accuracy', 0):.1f}%")
            lines.append(f"RMSE: {data.get('rmse', 0):.2f}")
            lines.append(f"MAE: {data.get('mae', 0):.2f}")
            lines.append(f"Predictions Count: {data.get('predictions_count', 0)}")

        elif data_type == "correlations":
            for indicator, corr in data.get("correlations", {}).items():
                strength = corr.get("strength", "weak")
                value = corr.get("value", 0)
                lines.append(f"{indicator}: {value:+.2f} ({strength})")

        elif data_type == "regimes":
            regimes = data.get("regimes", [])
            lines.append(f"Regimes Found: {len(regimes)}")
            if regimes:
                current = regimes[0]
                lines.append(f"Current Regime: {current.get('regime_type', 'unknown').upper()}")
                lines.append(f"Duration: {current.get('duration_days', 0)} days")
                lines.append(f"Avg Return: {current.get('avg_return', 0):.2f}%")

        return lines


# ============================================
# SINGLETON INSTANCE
# ============================================

export_service = ExportService()