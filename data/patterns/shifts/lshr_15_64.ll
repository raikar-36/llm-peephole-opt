define i64 @pattern_lshr_15_64(i64 %x) {
entry:
  %result = lshr i64 %x, 15
  ret i64 %result
}
