define i32 @pattern_ashr_15_32(i32 %x) {
entry:
  %result = ashr i32 %x, 15
  ret i32 %result
}
