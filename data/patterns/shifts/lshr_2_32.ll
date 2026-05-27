define i32 @pattern_lshr_2_32(i32 %x) {
entry:
  %result = lshr i32 %x, 2
  ret i32 %result
}
