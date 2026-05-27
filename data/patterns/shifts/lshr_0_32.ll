define i32 @pattern_lshr_0_32(i32 %x) {
entry:
  %result = lshr i32 %x, 0
  ret i32 %result
}
