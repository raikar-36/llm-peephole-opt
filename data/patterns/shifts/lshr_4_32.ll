define i32 @pattern_lshr_4_32(i32 %x) {
entry:
  %result = lshr i32 %x, 4
  ret i32 %result
}
