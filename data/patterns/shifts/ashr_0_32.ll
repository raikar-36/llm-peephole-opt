define i32 @pattern_ashr_0_32(i32 %x) {
entry:
  %result = ashr i32 %x, 0
  ret i32 %result
}
