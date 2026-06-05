Feature: 取得購物車
  作為購物車使用者
  我希望能查詢自己的購物車
  以便確認目前有哪些商品

  Background:
    Given 購物車服務使用空的儲存庫

  Scenario: 取得空購物車
    When 使用者 "user123" 取得購物車
    Then 購物車應有 0 個項目
    And 購物車總金額應為 0
