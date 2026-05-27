define i32 @pattern_lshr_15_32(i32 %x) {
entry:
  %result = lshr i32 %x, 15
  ret i32 %result
}
