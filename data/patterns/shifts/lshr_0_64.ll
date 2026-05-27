define i64 @pattern_lshr_0_64(i64 %x) {
entry:
  %result = lshr i64 %x, 0
  ret i64 %result
}
