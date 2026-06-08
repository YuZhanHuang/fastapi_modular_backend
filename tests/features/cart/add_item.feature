Feature: 加入購物車項目
  作為購物車使用者
  我希望能將商品加入購物車
  以便正確計算總金額

  Background:
    Given 購物車服務使用空的儲存庫

  Scenario: 成功加入商品
    When 使用者 "user123" 加入商品 "prod456" 數量 2 單價 1000
    Then 購物車總金額應為 2000

  Scenario: 數量無效
    When 使用者 "user123" 嘗試加入商品 "prod456" 數量 0 單價 1000
    Then 應拋出 InvalidQuantityError
