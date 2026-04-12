import pandas as pd
from typing import Dict, Optional, Any
import datetime

class DamodaranWACCProvider:
    """
    Provides WACC calculations based on Damodaran NYU Stern methodology.
    Supports industry-level unlevered betas, country risk premiums for Thailand,
    and ICR-based default spreads for cost of debt.
    """

    # Industry Unlevered Beta Mapping (Emerging Markets, Jan 2026)
    # Source: docs/damodaran-stern-datasets-thai-set.md
    UNLEVERED_BETAS = {
        'Advertising Agencies': 0.70,
        'Airports & Air Services': 0.65,
        'Apparel Manufacturing': 0.75,
        'Auto Parts': 0.80,
        'Banks - Regional': 0.12, # Low unlevered beta for banks
        'Beverages - Non-Alcoholic': 0.55,
        'Building Products & Equipment': 0.70,
        'Capital Markets': 0.85,
        'Chemicals': 0.75,
        'Computer Hardware': 0.90,
        'Confectioners': 0.55,
        'Conglomerates': 0.65,
        'Credit Services': 0.80,
        'Department Stores': 0.60,
        'Drug Manufacturers - Specialty & Generic': 0.75,
        'Electrical Equipment & Parts': 0.80,
        'Electronic Components': 0.95,
        'Engineering & Construction': 0.40, # Often low unlevered
        'Entertainment': 0.85,
        'Farm Products': 0.60,
        'Grocery Stores': 0.50,
        'Home Improvement Retail': 0.62,
        'Industry': 0.70,
        'Insurance - Life': 0.15,
        'Lodging': 0.52,
        'Marine Shipping': 0.75,
        'Medical Care Facilities': 0.62,
        'Metal Fabrication': 0.75,
        'Oil & Gas E&P': 0.75,
        'Oil & Gas Integrated': 0.70,
        'Oil & Gas Refining & Marketing': 0.70,
        'Packaged Foods': 0.56,
        'Packaging & Containers': 0.56,
        'Railroads': 0.60,
        'Real Estate - Development': 0.39,
        'Real Estate - Diversified': 0.40,
        'Real Estate Services': 0.65,
        'Rental & Leasing Services': 0.65,
        'Resorts & Casinos': 0.80,
        'Specialty Chemicals': 0.80,
        'Specialty Retail': 0.70,
        'Telecom Services': 0.57,
        'Textile Manufacturing': 0.75,
        'Thermal Coal': 0.70,
        'Utilities - Independent Power Producers': 0.55,
        'Utilities - Regulated Electric': 0.45,
        'Utilities - Renewable': 0.60,
        'DEFAULT': 0.75
    }

    # Thai 10Y Bond Yields (Approximated history)
    THAI_10Y_YIELDS = {
        2016: 0.022,
        2017: 0.025,
        2018: 0.028,
        2019: 0.020,
        2020: 0.013,
        2021: 0.018,
        2022: 0.025,
        2023: 0.030,
        2024: 0.032,
        2025: 0.035,
        2026: 0.035
    }

    # Thailand Equity Risk Premium (CDS-based from doc)
    THAILAND_ERP = 0.0587

    # Tax Rate
    THAILAND_TAX_RATE = 0.20

    def __init__(self):
        pass

    def get_risk_free_rate(self, date: Any) -> float:
        """Get Thai 10Y bond yield for the given date."""
        if isinstance(date, str):
            year = pd.to_datetime(date).year
        elif hasattr(date, 'year'):
            year = date.year
        else:
            year = 2025
        
        return self.THAI_10Y_YIELDS.get(year, 0.035)

    def get_unlevered_beta(self, industry: str) -> float:
        """Get industry unlevered beta."""
        return self.UNLEVERED_BETAS.get(industry, self.UNLEVERED_BETAS['DEFAULT'])

    def get_default_spread(self, icr: float) -> float:
        """Get default spread based on Interest Coverage Ratio (ICR)."""
        if icr > 8.5: return 0.0085
        if icr > 6.5: return 0.0100
        if icr > 5.5: return 0.0110
        if icr > 4.25: return 0.0120
        if icr > 3.0: return 0.0150
        if icr > 2.5: return 0.0200
        if icr > 2.25: return 0.0300
        if icr > 2.0: return 0.0400
        if icr > 1.75: return 0.0450
        if icr > 1.5: return 0.0550
        if icr > 1.25: return 0.0650
        if icr > 0.8: return 0.0850
        if icr > 0.5: return 0.1000
        return 0.1500

    def calculate_wacc(self, 
                       industry: str, 
                       equity_value: float, 
                       total_debt: float, 
                       ebit: float, 
                       interest_expense: float,
                       date: Any = None) -> Dict[str, float]:
        """
        Calculate WACC according to Damodaran's principles.
        """
        rf = self.get_risk_free_rate(date)
        unlevered_beta = self.get_unlevered_beta(industry)
        
        # Levered Beta = Unlevered Beta * (1 + (1 - tax) * D/E)
        de_ratio = total_debt / equity_value if equity_value > 0 else 0
        levered_beta = unlevered_beta * (1 + (1 - self.THAILAND_TAX_RATE) * de_ratio)
        
        # Cost of Equity (Ke) = Rf + Beta * ERP
        cost_of_equity = rf + levered_beta * self.THAILAND_ERP
        
        # Cost of Debt (Rd) = Rf + Default Spread
        icr = ebit / abs(interest_expense) if interest_expense != 0 else 999
        if icr < 0: icr = 0 # Distressed
        
        default_spread = self.get_default_spread(icr)
        cost_of_debt = rf + default_spread
        
        # Weights
        total_capital = equity_value + total_debt
        if total_capital > 0:
            we = equity_value / total_capital
            wd = total_debt / total_capital
            
            wacc = (cost_of_equity * we) + (cost_of_debt * (1 - self.THAILAND_TAX_RATE) * wd)
        else:
            wacc = cost_of_equity
            
        return {
            'wacc': wacc,
            'cost_of_equity': cost_of_equity,
            'cost_of_debt': cost_of_debt,
            'levered_beta': levered_beta,
            'unlevered_beta': unlevered_beta,
            'risk_free_rate': rf,
            'icr': icr
        }

if __name__ == "__main__":
    # Test
    provider = DamodaranWACCProvider()
    res = provider.calculate_wacc('Banks - Regional', 1000, 200, 100, 10, '2024-01-01')
    print(res)
