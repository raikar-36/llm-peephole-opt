define i32 @pattern_lshr_7_32(i32 %x) {
entry:
  %result = lshr i32 %x, 7
  ret i32 %result
}
