define i64 @pattern_lshr_2_64(i64 %x) {
entry:
  %result = lshr i64 %x, 2
  ret i64 %result
}
