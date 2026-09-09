import { describe, expect, it } from 'vitest';
import {
  HORIZON_LABELS,
  HORIZON_SHORT_LABELS,
  THRESHOLD_OPTIONS,
  THRESHOLD_LABELS,
  DEFAULT_CONFIDENCE_CHANGE,
  formatPredictionAlertHeadline,
  getRecommendation,
  formatConfidenceDisplay,
} from '../predictionAlertRule';

describe('predictionAlertRule', () => {
  describe('Constants', () => {
    it('should have correct horizon labels', () => {
      expect(HORIZON_LABELS['24h']).toBe('24 hours');
      expect(HORIZON_LABELS['7d']).toBe('7 days');
    });

    it('should have correct short horizon labels', () => {
      expect(HORIZON_SHORT_LABELS['24h']).toBe('24h');
      expect(HORIZON_SHORT_LABELS['7d']).toBe('7d');
    });

    it('should have correct threshold options', () => {
      expect(THRESHOLD_OPTIONS).toEqual([1, 2, 5, 10]);
    });

    it('should have correct threshold labels', () => {
      expect(THRESHOLD_LABELS[1]).toBe('1%');
      expect(THRESHOLD_LABELS[2]).toBe('2%');
      expect(THRESHOLD_LABELS[5]).toBe('5%');
      expect(THRESHOLD_LABELS[10]).toBe('10%');
    });

    it('should have default confidence change', () => {
      expect(DEFAULT_CONFIDENCE_CHANGE).toBe(5);
    });
  });

  describe('formatPredictionAlertHeadline', () => {
    it('should format headline correctly for 24h horizon', () => {
      const result = formatPredictionAlertHeadline(5, '24h');
      expect(result).toBe('Prediction changes by 5% or more (24h)');
    });

    it('should format headline correctly for 7d horizon', () => {
      const result = formatPredictionAlertHeadline(10, '7d');
      expect(result).toBe('Prediction changes by 10% or more (7d)');
    });
  });

  describe('getRecommendation', () => {
    it('should return bullish recommendation for positive change', () => {
      expect(getRecommendation(68000, 70123.75)).toContain('Bullish');
    });

    it('should return bearish recommendation for negative change', () => {
      expect(getRecommendation(71500, 68900)).toContain('Bearish');
    });

    it('should return minor change for very small differences', () => {
      // 0.5 point change out of 70000 is ~0.0007% - definitely minor
      expect(getRecommendation(70000, 70000.5)).toBe('Minor change detected');
    });

    it('should return monitor for moderate changes', () => {
      // 500 point change out of 70000 is ~0.7% - should be "Consider monitoring"
      // But since 0.7% < 2%, it returns "Consider monitoring"
      expect(getRecommendation(70000, 70500)).toBe('Consider monitoring');
    });

    it('should return bullish for large positive changes', () => {
      // 5000 point change out of 70000 is ~7% - definitely bullish
      expect(getRecommendation(70000, 75000)).toContain('Bullish');
    });
  });

  describe('formatConfidenceDisplay', () => {
    it('should format confidence with percentage', () => {
      expect(formatConfidenceDisplay(74)).toBe('74%');
      expect(formatConfidenceDisplay(85.5)).toBe('86%');
    });
  });
});
