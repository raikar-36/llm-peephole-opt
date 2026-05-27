define i32 @pattern_lshr_31_32(i32 %x) {
entry:
  %result = lshr i32 %x, 31
  ret i32 %result
}
