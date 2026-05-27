define i64 @pattern_lshr_3_64(i64 %x) {
entry:
  %result = lshr i64 %x, 3
  ret i64 %result
}
