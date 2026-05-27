define i64 @pattern_lshr_7_64(i64 %x) {
entry:
  %result = lshr i64 %x, 7
  ret i64 %result
}
