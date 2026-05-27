define i64 @pattern_lshr_4_64(i64 %x) {
entry:
  %result = lshr i64 %x, 4
  ret i64 %result
}
