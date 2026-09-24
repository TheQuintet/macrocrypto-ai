import pandas as pd


class TargetGenerator:
  """Generates and aligns the next-day Bitcoin price target (y_t = Price_{t+1})

  for supervised machine learning tasks, ensuring zero look-ahead bias
  and properly managing the unlabeled trailing inference frontier.
  """

  def __init__(self, price_column: str = "btc_price"):
      self.price_column = price_column

  def generate_target(self, df: pd.DataFrame) -> pd.DataFrame:
    """Appends the next-day target column ('target_next_price') to the DataFrame.

    The final row will naturally contain a NaN target representing the live,
    unlabeled inference frontier.
    """
    if self.price_column not in df.columns:
      raise ValueError(
          f"Price column '{self.price_column}' not found in DataFrame."
          f" Available columns: {list(df.columns)}"
      )

    df_out = df.copy()
    # Shift price backwards by 1 to align day t features with day t+1 target
    df_out["target_next_price"] = df_out[self.price_column].shift(-1)
    return df_out

  def split_supervised_data(self, df: pd.DataFrame):
    """Splits the dataframe into supervised training/validation/test data

    (excluding the trailing NaN row) and the live inference row.
    """
    df_with_target = self.generate_target(df)

    # The last row has a NaN target (no t+1 price available yet)
    live_frontier_row = df_with_target.iloc[[-1]]
    supervised_df = df_with_target.iloc[:-1].copy()

    return supervised_df, live_frontier_row