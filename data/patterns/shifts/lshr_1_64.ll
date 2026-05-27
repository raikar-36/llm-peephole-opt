define i64 @pattern_lshr_1_64(i64 %x) {
entry:
  %result = lshr i64 %x, 1
  ret i64 %result
}
